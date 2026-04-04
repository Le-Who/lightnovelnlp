"""Quick diagnostic: verifies google-genai SDK is installed and functional."""

from google import genai
from google.genai import types

print(f"google-genai version: {genai.__version__}")

try:
    cfg = types.GenerateContentConfig(response_mime_type="application/json")
    print("GenerateContentConfig(response_mime_type=...): OK")
except Exception as e:
    print(f"GenerateContentConfig error: {e}")

try:
    thinking = types.ThinkingConfig(thinking_budget=1024)
    print("ThinkingConfig(thinking_budget=1024): OK")
except Exception as e:
    print(f"ThinkingConfig error: {e}")
