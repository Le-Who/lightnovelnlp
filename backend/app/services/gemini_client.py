"""
GeminiClient v2 — Task-aware, thread-safe Gemini API client.

Key design decisions:
- No mutable instance state (no self.client, no self.current_key_index).
- genai.Client is created per-request with the selected API key (thread-safe).
- Rate limiting is per-key per-model via Redis (RPM + RPD).
- ThinkingConfig auto-detects Gemini 3.x vs 2.5.x series.
- Flat retry loop: models → keys → next model (no nested try/except hell).
- Stage-aware logging: every log line includes [GEMINI:{task_type}].
"""

from __future__ import annotations

import hashlib
import logging
import time
import warnings
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from google import genai
from google.genai import types
import pytz

# Suppress Pydantic warnings from google-genai types
warnings.filterwarnings("ignore", category=UserWarning, module="pydantic")
logging.getLogger("google.genai.types").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
warnings.filterwarnings(
    "ignore", message=".*shadows an attribute.*", category=UserWarning
)

logger = logging.getLogger(__name__)

from app.core.config import settings
from app.services.cache_service import cache_service
from app.core.exceptions import APIKeyExhausted


def _key_hash(api_key: str) -> str:
    """Short deterministic hash of an API key for Redis keys (avoids storing raw keys)."""
    return hashlib.sha256(api_key.encode()).hexdigest()[:12]


def _now_minute() -> str:
    """Current UTC minute window as YYYYMMDD_HHMM."""
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def _today_mv(tz: Any) -> str:
    """Today's date in Mountain View timezone."""
    return datetime.now(tz).strftime("%Y-%m-%d")


def _seconds_until_mv_midnight(tz: Any) -> int:
    """Seconds remaining until midnight in Mountain View timezone."""
    now_mv = datetime.now(tz)
    tomorrow_mv = now_mv.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(
        days=1
    )
    return int((tomorrow_mv - now_mv).total_seconds())


class GeminiClient:
    """Thread-safe, task-aware Gemini API client with per-key per-model rate limiting."""

    def __init__(self):
        self.api_keys: List[str] = settings.GEMINI_API_KEYS
        self.key_hashes: List[str] = [_key_hash(k) for k in self.api_keys]
        self.reset_tz = pytz.timezone(settings.GEMINI_API_RESET_TIMEZONE)
        self.cooldown_minutes = settings.GEMINI_API_COOLDOWN_MINUTES

        # Per-model limits (from config, user provides actuals)
        self.rpm_limits: Dict[str, int] = settings.GEMINI_RPM_LIMITS_MAP
        self.rpd_limits: Dict[str, int] = settings.GEMINI_RPD_LIMITS_MAP

        # Fallback chain
        self.fallback_models: List[str] = settings.GEMINI_FALLBACK_MODELS_LIST

        if not self.api_keys:
            raise ValueError("No Gemini API keys provided in GEMINI_API_KEYS_RAW")

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    def complete(
        self,
        prompt: str,
        *,
        task_type: str = "default",
        model_override: str | None = None,
        thinking_override: str | None = None,
        max_tokens: int | None = None,
        generation_config: Dict[str, Any] | None = None,
        response_schema: Any = None,
    ) -> Any:
        """
        Execute a Gemini completion with task-aware model routing and rate limiting.

        Args:
            prompt: The prompt text or structured content.
            task_type: Pipeline stage — "extraction", "translation", "summarization", "relationships", "default".
            model_override: Explicit model name (highest priority). Falls back to settings if None.
            thinking_override: Explicit thinkingLevel (or budget for 2.5). Falls back to settings if None.
            max_tokens: Explicit max_output_tokens. Falls back to per-task default if None.
            generation_config: Additional GenerateContentConfig kwargs (merged with built config).
            response_schema: Pydantic model or dict for structured output (response_mime_type=application/json).

        Returns:
            Parsed response object (if response_schema) or raw text string.

        Raises:
            APIKeyExhausted: All keys/models exhausted after retries.
            RateLimitExceeded: Pre-flight rate limit check failed on all keys.
        """
        # Resolve defaults from settings
        primary_model = model_override or settings.get_model_for_task(task_type)
        thinking = thinking_override or settings.get_thinking_for_task(task_type)
        effective_max_tokens = (
            max_tokens
            if max_tokens is not None
            else settings.get_max_tokens_for_task(task_type)
        )

        # Build model chain: primary → fallbacks
        model_chain = [primary_model] + [
            m for m in self.fallback_models if m != primary_model
        ]

        last_error: Exception | None = None

        for model_name in model_chain:
            result = self._try_model_across_keys(
                model_name=model_name,
                prompt=prompt,
                task_type=task_type,
                thinking=thinking,
                max_tokens=effective_max_tokens,
                generation_config=generation_config,
                response_schema=response_schema,
            )
            if result is not _SENTINEL:
                return result
            # If _try_model_across_keys returned _SENTINEL, all keys failed for this model.
            # Try next model in fallback chain.
            logger.warning(
                f"[GEMINI:{task_type}] All keys failed for {model_name}, trying next fallback..."
            )

        raise APIKeyExhausted(
            f"All models and keys exhausted for task '{task_type}'. "
            f"Chain: {[m for m in model_chain]}"
        )

    def get_usage_stats(self) -> Dict[str, Any]:
        """Returns current rate limit usage for all keys and models."""
        today = _today_mv(self.reset_tz)
        current_minute = _now_minute()

        all_models = list(
            set(
                [
                    settings.GEMINI_MODEL_EXTRACTION,
                    settings.GEMINI_MODEL_TRANSLATION,
                    settings.GEMINI_MODEL_SUMMARIZATION,
                    settings.GEMINI_MODEL_RELATIONSHIPS,
                ]
                + self.fallback_models
            )
        )

        stats: Dict[str, Any] = {
            "reset_timezone": settings.GEMINI_API_RESET_TIMEZONE,
            "current_time_mv": datetime.now(self.reset_tz).isoformat(),
            "total_keys": len(self.api_keys),
            "models": {},
            "keys": [],
        }

        # Per-model aggregate stats
        for model in all_models:
            stats["models"][model] = {
                "rpm_limit": self.rpm_limits.get(model, "unknown"),
                "rpd_limit": self.rpd_limits.get(model, "unknown"),
            }

        # Per-key stats
        for i, kh in enumerate(self.key_hashes):
            key_info: Dict[str, Any] = {
                "index": i,
                "in_cooldown": self._is_key_in_cooldown(kh),
                "models": {},
            }
            for model in all_models:
                rpm_key = f"gemini_rpm:{kh}:{model}:{current_minute}"
                rpd_key = f"gemini_rpd:{kh}:{model}:{today}"
                key_info["models"][model] = {
                    "rpm_current": cache_service.get_quiet(rpm_key) or 0,
                    "rpd_current": cache_service.get_quiet(rpd_key) or 0,
                }
            stats["keys"].append(key_info)

        # Per-task stage stats
        stats["stages"] = {}
        for task in ["extraction", "translation", "summarization", "relationships"]:
            stage_key = f"gemini_stage:{task}:{today}"
            stats["stages"][task] = cache_service.get_quiet(stage_key) or 0

        return stats

    # ──────────────────────────────────────────────────────────────
    # Internal: Model × Keys loop
    # ──────────────────────────────────────────────────────────────

    def _try_model_across_keys(
        self,
        model_name: str,
        prompt: str,
        task_type: str,
        thinking: str | None,
        max_tokens: int,
        generation_config: Dict[str, Any] | None,
        response_schema: Any,
    ) -> Any:
        """Try all keys for a specific model. Returns _SENTINEL if all fail."""
        for key_idx, (api_key, kh) in enumerate(zip(self.api_keys, self.key_hashes)):
            # Skip keys in cooldown
            if self._is_key_in_cooldown(kh):
                logger.debug(
                    f"[GEMINI:{task_type}] Key #{key_idx} in cooldown, skipping"
                )
                continue

            # Pre-flight rate limit check for this key × model
            if not self._check_rate_limits(kh, model_name, task_type):
                continue  # This key is at RPM/RPD limit for this model

            try:
                # Create ephemeral client (thread-safe, no shared state)
                client = genai.Client(api_key=api_key)
                config = self._build_config(
                    model_name=model_name,
                    thinking=thinking,
                    max_tokens=max_tokens,
                    generation_config=generation_config,
                    response_schema=response_schema,
                )

                logger.info(f"[GEMINI:{task_type}] → {model_name} (key #{key_idx})")
                start_time = time.monotonic()

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=config,
                )

                elapsed_ms = int((time.monotonic() - start_time) * 1000)

                # Record successful usage
                self._record_usage(kh, model_name, task_type)

                # Process response
                result = self._extract_result(
                    response, model_name, task_type, max_tokens
                )
                logger.info(
                    f"[GEMINI:{task_type}] ← OK from {model_name} "
                    f"(key #{key_idx}, {elapsed_ms}ms)"
                )
                return result

            except Exception as e:
                error_str = str(e)
                if self._is_rate_limit_error(error_str):
                    # 429 from Google → soft cooldown this key (NOT the whole day)
                    logger.warning(
                        f"[GEMINI:{task_type}] 429 on {model_name} key #{key_idx}: {e}"
                    )
                    self._put_key_in_cooldown(kh)
                    continue  # Try next key for this same model
                else:
                    # Non-rate-limit error (content filter, server error, bad request) → skip model
                    logger.error(
                        f"[GEMINI:{task_type}] Error on {model_name} key #{key_idx}: {e}"
                    )
                    # For non-429 errors, trying another key won't help — break to next model
                    return _SENTINEL

        # All keys exhausted for this model
        return _SENTINEL

    # ──────────────────────────────────────────────────────────────
    # Rate Limiting (per-key per-model)
    # ──────────────────────────────────────────────────────────────

    def _check_rate_limits(
        self, key_hash: str, model_name: str, task_type: str
    ) -> bool:
        """
        Pre-flight check: is this key within RPM/RPD limits for this model?
        Returns True if OK to proceed, False if limit reached.
        """
        current_minute = _now_minute()
        today = _today_mv(self.reset_tz)

        # RPM check
        rpm_limit = self.rpm_limits.get(model_name, 10)  # conservative default
        rpm_key = f"gemini_rpm:{key_hash}:{model_name}:{current_minute}"
        current_rpm = cache_service.get_quiet(rpm_key) or 0
        if current_rpm >= rpm_limit:
            logger.debug(
                f"[GEMINI:{task_type}] RPM limit ({current_rpm}/{rpm_limit}) "
                f"for {model_name} on key {key_hash[:6]}"
            )
            return False

        # RPD check
        rpd_limit = self.rpd_limits.get(model_name, 500)  # conservative default
        rpd_key = f"gemini_rpd:{key_hash}:{model_name}:{today}"
        current_rpd = cache_service.get_quiet(rpd_key) or 0
        if current_rpd >= rpd_limit:
            logger.debug(
                f"[GEMINI:{task_type}] RPD limit ({current_rpd}/{rpd_limit}) "
                f"for {model_name} on key {key_hash[:6]}"
            )
            return False

        return True

    def _record_usage(self, key_hash: str, model_name: str, task_type: str) -> None:
        """Record successful request in RPM, RPD, and stage counters."""
        current_minute = _now_minute()
        today = _today_mv(self.reset_tz)
        rpd_ttl = _seconds_until_mv_midnight(self.reset_tz) + 3600  # buffer

        # RPM (1-minute window)
        rpm_key = f"gemini_rpm:{key_hash}:{model_name}:{current_minute}"
        cache_service.increment_counter(rpm_key, ttl=65)

        # RPD (daily)
        rpd_key = f"gemini_rpd:{key_hash}:{model_name}:{today}"
        cache_service.increment_counter(rpd_key, ttl=rpd_ttl)

        # Stage counter (observability)
        stage_key = f"gemini_stage:{task_type}:{today}"
        cache_service.increment_counter(stage_key, ttl=rpd_ttl)

    # ──────────────────────────────────────────────────────────────
    # Cooldown Management
    # ──────────────────────────────────────────────────────────────

    def _is_key_in_cooldown(self, key_hash: str) -> bool:
        """Check if a key is in soft cooldown (after 429)."""
        cooldown_key = f"gemini_cooldown:{key_hash}"
        cooldown_until = cache_service.get_quiet(cooldown_key)
        if not cooldown_until:
            return False
        try:
            cooldown_time = datetime.fromisoformat(str(cooldown_until))
            now_dt = (
                datetime.now(cooldown_time.tzinfo)
                if cooldown_time.tzinfo
                else datetime.now(self.reset_tz)
            )
            return now_dt < cooldown_time
        except Exception:
            return False

    def _put_key_in_cooldown(self, key_hash: str) -> None:
        """Soft cooldown: key is unavailable for N minutes (not the whole day)."""
        cooldown_key = f"gemini_cooldown:{key_hash}"
        cooldown_until = (
            datetime.now(self.reset_tz) + timedelta(minutes=self.cooldown_minutes)
        ).isoformat()
        ttl_seconds = self.cooldown_minutes * 60 + 60  # buffer
        cache_service.set(cooldown_key, cooldown_until, ttl=ttl_seconds)
        logger.info(f"Key {key_hash[:6]} in cooldown for {self.cooldown_minutes} min")

    # ──────────────────────────────────────────────────────────────
    # Config Builder (ThinkingConfig autodetect)
    # ──────────────────────────────────────────────────────────────

    def _build_config(
        self,
        model_name: str,
        thinking: str | None,
        max_tokens: int,
        generation_config: Dict[str, Any] | None,
        response_schema: Any,
    ) -> types.GenerateContentConfig | None:
        """Build GenerateContentConfig with thinking autodetect."""
        config_args: Dict[str, Any] = {}

        # Merge caller-provided generation_config
        if generation_config:
            config_args.update(generation_config)

        # max_output_tokens
        config_args["max_output_tokens"] = max_tokens

        # ThinkingConfig (auto-detect series)
        if thinking:
            thinking_config = self._build_thinking_config(model_name, thinking)
            if thinking_config:
                config_args["thinking_config"] = thinking_config

        # Structured output
        if response_schema:
            config_args["response_mime_type"] = "application/json"
            config_args["response_schema"] = response_schema

        return types.GenerateContentConfig(**config_args) if config_args else None

    def _build_thinking_config(
        self, model_name: str, level_or_budget: str
    ) -> types.ThinkingConfig | None:
        """
        Auto-detect Gemini generation and build correct ThinkingConfig.
        - Gemini 3.x → thinkingLevel (minimal/low/medium/high)
        - Gemini 2.5.x → thinkingBudget (int, mapped from level names)
        """
        is_gemini_3 = any(tag in model_name for tag in ["gemini-3", "gemini-3."])

        if is_gemini_3:
            # Validate level
            valid_levels = {"minimal", "low", "medium", "high"}
            level = (
                level_or_budget.lower()
                if isinstance(level_or_budget, str)
                else "medium"
            )
            if level not in valid_levels:
                logger.warning(
                    f"Invalid thinkingLevel '{level}', defaulting to 'medium'"
                )
                level = "medium"
            return types.ThinkingConfig(thinking_level=level)
        else:
            # Gemini 2.5.x: map named levels to budget integers
            budget_map = {"minimal": 0, "low": 1024, "medium": 4096, "high": 8192}
            if (
                isinstance(level_or_budget, str)
                and level_or_budget.lower() in budget_map
            ):
                budget = budget_map[level_or_budget.lower()]
            elif isinstance(level_or_budget, str) and level_or_budget.isdigit():
                budget = int(level_or_budget)
            else:
                budget = -1  # Dynamic thinking (default for 2.5)
            return types.ThinkingConfig(thinking_budget=budget)

    # ──────────────────────────────────────────────────────────────
    # Response Extraction
    # ──────────────────────────────────────────────────────────────

    def _extract_result(
        self, response: Any, model_name: str, task_type: str, max_tokens: int
    ) -> Any:
        """Extract text or parsed result from a successful Gemini response."""
        candidate = response.candidates[0]

        # Check finish reason
        if candidate.finish_reason == "MAX_TOKENS":
            logger.error(
                f"[GEMINI:{task_type}] Response truncated (MAX_TOKENS, limit={max_tokens}) "
                f"from {model_name}"
            )
        elif candidate.finish_reason not in ("STOP", "OTHER", None):
            logger.warning(
                f"[GEMINI:{task_type}] Unexpected finish_reason: {candidate.finish_reason}"
            )

        # Prefer parsed (structured output)
        if hasattr(response, "parsed") and response.parsed:
            return response.parsed

        # Fallback to text concatenation
        text_parts: list[str] = []
        if candidate.content and candidate.content.parts:
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

        result_text = "".join(text_parts)
        logger.info(
            f"[GEMINI:{task_type}] Response: {len(result_text)} chars from {model_name}"
        )
        return result_text

    # ──────────────────────────────────────────────────────────────
    # Utilities
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _is_rate_limit_error(error_str: str) -> bool:
        """Detect Google 429 / RESOURCE_EXHAUSTED errors."""
        markers = ("429", "RESOURCE_EXHAUSTED", "rate limit", "quota exceeded")
        error_lower = error_str.lower()
        return any(m.lower() in error_lower for m in markers)


# Sentinel object for internal signaling (model failed, try next)
_SENTINEL = object()

# Global client instance
gemini_client = GeminiClient()
