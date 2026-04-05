import io
import logging
from typing import List
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models.glossary import (
    GlossaryTerm,
)
from app.models.project import Chapter, Project
from app.schemas.project import (
    ChapterCreate,
    ChapterList,
    ChapterRead,
    ChapterUpdate,
    ProjectCreate,
    ProjectRead,
)

try:
    import pypdf
except Exception:
    pypdf = None

import html
import re
from html.parser import HTMLParser

from app.core.nlp_pipeline.context_summarizer import context_summarizer
from app.services.project_service import ProjectService

try:
    import ebooklib
    from ebooklib import epub
except ImportError:
    ebooklib = None
    epub = None

from app.core.regex_utils import safe_finditer

router = APIRouter()
logger = logging.getLogger(__name__)


class HTMLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self, d):
        self.text.append(d)

    def get_data(self):
        return "".join(self.text)


def _strip_html_tags(html_content: str) -> str:
    s = HTMLStripper()
    s.feed(html_content)
    return html.unescape(s.get_data()).strip()


@router.get("/", response_model=List[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> List[Project]:
    return ProjectService.get_projects(db)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    return ProjectService.create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> Project:
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectCreate, db: Session = Depends(get_db)
) -> Project:  # Using ProjectCreate as base or ProjectUpdate if defined in schema

    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    ProjectService.delete_project(db, project_id)


# Главы
@router.get("/{project_id}/chapters", response_model=List[ChapterList])
def list_chapters(
    project_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, gt=0, le=1000),
    offset: int = Query(default=0, ge=0),
    search: str | None = None,
    sort_by: str = Query(default="id"),
    order: str = Query(default="asc"),
) -> List[ChapterList]:
    """Получить все главы проекта (пагинация/поиск/сортировка)."""
    q = db.query(
        Chapter.id,
        Chapter.project_id,
        Chapter.title,
        Chapter.order,
        Chapter.analysis_status,
        Chapter.translation_status,
        Chapter.created_at,
        Chapter.processed_at,
        Chapter.summary,
        func.length(Chapter.original_text).label("original_text_length"),
        func.length(Chapter.translated_text).label("translated_text_length"),
    ).filter(Chapter.project_id == project_id)

    if search:
        s = f"%{search}%"
        q = q.filter(or_(Chapter.title.ilike(s), Chapter.original_text.ilike(s)))
    sort_map = {
        "id": Chapter.id,
        "title": Chapter.title,
        "order": Chapter.order,
        "created_at": Chapter.created_at,
        "processed_at": Chapter.processed_at,
    }
    sort_col = sort_map.get(sort_by, Chapter.id)
    q = q.order_by(sort_col.desc() if order.lower() == "desc" else sort_col.asc())
    if offset:
        q = q.offset(offset)
    if limit:
        q = q.limit(limit)
    return q.all()


@router.post(
    "/{project_id}/chapters",
    response_model=ChapterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_chapter(
    project_id: int, payload: ChapterCreate, db: Session = Depends(get_db)
) -> Chapter:
    """Создать новую главу в проекте."""
    # Проверяем, что проект существует
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Определяем порядок новой главы
    max_order = (
        db.query(func.max(Chapter.order))
        .filter(Chapter.project_id == project_id)
        .scalar()
        or 0
    )

    chapter = Chapter(
        project_id=project_id,
        title=payload.title,
        original_text=payload.original_text,
        order=max_order + 1,
    )

    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.post(
    "/{project_id}/chapters/upload",
    response_model=ChapterRead,
    status_code=status.HTTP_201_CREATED,
)
def create_chapter_from_file(
    project_id: int,
    title: str = "Глава 1",  # Default title for uploaded chapters
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> Chapter:
    """Создать главу из файла (txt, pdf, rtf, doc - простая поддержка)."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content_bytes = file.file.read()
    text = ""
    filename = (file.filename or "").lower()
    if filename.endswith(".txt"):
        text = content_bytes.decode(errors="ignore")
    elif filename.endswith(".pdf") and pypdf is not None:
        try:
            reader = pypdf.PdfReader(io.BytesIO(content_bytes))
            pages = [page.extract_text() or "" for page in reader.pages]
            text = "\n".join(pages)
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to parse PDF")
    elif filename.endswith(".rtf"):
        # Простейшее извлечение: удалим RTF теги
        raw = content_bytes.decode(errors="ignore")
        text = re.sub(r"\\[a-zA-Z]+[0-9]* ?|[{}]", "", raw)
    elif filename.endswith(".doc"):
        # .doc без внешних зависимостей корректно не парсится; попытаемся как текст
        text = content_bytes.decode(errors="ignore")
    elif filename.endswith(".epub") and epub is not None:
        try:
            # Парсинг EPUB и объединение всех глав в один текст
            with open("temp.epub", "wb") as f:
                f.write(content_bytes)
            book = epub.read_epub("temp.epub")
            parts = []
            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                raw_html = item.get_content().decode("utf-8", errors="ignore")
                parts.append(_strip_html_tags(raw_html))
            text = "\n\n".join(parts)
            import os

            if os.path.exists("temp.epub"):
                os.remove("temp.epub")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse EPUB: {e}")
    else:
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Use txt/pdf/rtf/doc/epub"
        )

    if not text.strip():
        raise HTTPException(status_code=400, detail="File has no extractable text")

    # Определяем порядок новой главы
    max_order = (
        db.query(func.max(Chapter.order))
        .filter(Chapter.project_id == project_id)
        .scalar()
        or 0
    )

    chapter = Chapter(
        project_id=project_id, title=title, original_text=text, order=max_order + 1
    )
    db.add(chapter)
    db.commit()
    db.refresh(chapter)
    return chapter


@router.post("/{project_id}/upload_chapters")
def upload_chapters_from_file(
    project_id: int,
    file: UploadFile = File(...),
    chapter_pattern: str = Form(default="Глава \\d+"),
    db: Session = Depends(get_db),
):
    """Загрузить главы из текстового файла."""
    logger.debug("Receiving upload for project %s", project_id)
    logger.debug("Filename: %s, Content-Type: %s", file.filename, file.content_type)
    logger.debug("Chapter pattern: %s", chapter_pattern)

    # Проверяем существование проекта
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Проверяем тип файла
    filename = file.filename.lower()
    if not (filename.endswith(".txt") or filename.endswith(".epub")):
        raise HTTPException(
            status_code=400, detail="Only .txt and .epub files are supported"
        )

    try:
        content_bytes = file.file.read()
        created_chapters = []

        if filename.endswith(".epub") and epub is not None:
            logger.debug("Processing EPUB file")
            # Save to temporary file since ebooklib expects a file path
            with open("temp.epub", "wb") as f:
                f.write(content_bytes)

            book = epub.read_epub("temp.epub")

            for item in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
                raw_html = item.get_content().decode("utf-8", errors="ignore")
                chapter_text = _strip_html_tags(raw_html)
                if len(chapter_text.strip()) > 50:  # Skip tiny dummy files
                    created_chapters.append(chapter_text)

            import os

            if os.path.exists("temp.epub"):
                os.remove("temp.epub")

            if not created_chapters:
                raise HTTPException(
                    status_code=400, detail="No readable chapters found in EPUB"
                )

            # Create chapters from exact EPUB spine
            max_order = (
                db.query(func.max(Chapter.order))
                .filter(Chapter.project_id == project_id)
                .scalar()
                or 0
            )
            db_chapters = []
            for i, text in enumerate(created_chapters):
                # Optionally extract title from the first line or just use numbering
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                c_title = (
                    lines[0] if lines and len(lines[0]) < 100 else f"Глава {i + 1}"
                )
                ch = Chapter(
                    project_id=project_id,
                    title=c_title,
                    original_text=text,
                    order=max_order + 1 + i,
                )
                db.add(ch)
                db_chapters.append(ch)

            db.commit()
            return {
                "message": f"Successfully uploaded {len(db_chapters)} chapters from EPUB",
                "chapters_count": len(db_chapters),
            }

        else:
            # Читаем содержимое txt файла
            content = content_bytes.decode("utf-8")
        logger.debug("File content length: %d", len(content))

        # Разделяем текст на главы по паттерну
        pattern = re.compile(f"\\n({chapter_pattern})", re.IGNORECASE)
        # Находим все совпадения с их позициями
        try:
            matches = list(safe_finditer(pattern, content, timeout=10.0))
        except TimeoutError:
            raise HTTPException(
                status_code=400,
                detail="Chapter detection timed out. Please simplify your regex pattern or reduce file size.",
            )

        logger.debug("Found %d chapter matches", len(matches))

        if not matches:
            # Try fallback to just reading the whole file as one chapter if no pattern matches?
            # Or just error. User wants explicit error.
            logger.debug("No matches found for pattern '%s'", chapter_pattern)
            raise HTTPException(
                status_code=400,
                detail=f"No chapters found with the specified pattern: '{chapter_pattern}'",
            )

        created_chapters = []

        # Обрабатываем текст до первой главы
        first_match = matches[0]
        if first_match.start() > 0:
            intro_text = content[: first_match.start()].strip()
            if intro_text:
                intro_chapter = Chapter(
                    project_id=project_id,
                    title="Введение",
                    original_text=intro_text,
                    order=0,
                )
                db.add(intro_chapter)
                created_chapters.append(intro_chapter)

        # Обрабатываем найденные главы
        for i, match in enumerate(matches):
            chapter_title = match.group(1)

            # Определяем конец главы (до следующей главы или до конца файла)
            if i + 1 < len(matches):
                next_match = matches[i + 1]
                chapter_content = content[match.end() : next_match.start()].strip()
            else:
                chapter_content = content[match.end() :].strip()

            if chapter_content:  # Пропускаем пустые главы
                chapter = Chapter(
                    project_id=project_id,
                    title=chapter_title,
                    original_text=chapter_content,
                    order=len(created_chapters),
                )
                db.add(chapter)
                created_chapters.append(chapter)

        db.commit()

        return {
            "project_id": project_id,
            "chapters_created": len(created_chapters),
            "total_chapters": len(created_chapters),
            "pattern_used": chapter_pattern,
            "chapters": [
                {
                    "title": ch.title,
                    "order": ch.order,
                    "content_length": len(ch.original_text),
                }
                for ch in created_chapters
            ],
        }

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400, detail="File encoding error. Please use UTF-8 encoding."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        file.file.close()


@router.get("/{project_id}/chapters/{chapter_id}/download")
def download_chapter(project_id: int, chapter_id: int, db: Session = Depends(get_db)):
    """Скачать переведенную главу в формате TXT."""

    # Проверяем, что проект и глава существуют
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    chapter = db.get(Chapter, chapter_id)
    if not chapter or chapter.project_id != project_id:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if not chapter.translated_text:
        raise HTTPException(status_code=404, detail="Chapter not translated yet")

    # Формируем содержимое файла
    content = f"""Перевод главы: {chapter.title}
Проект: {project.name}
Жанр: {project.genre}

{chapter.translated_text}

---
Оригинальный текст:
{chapter.original_text}
"""

    # Подготавливаем безопасные заголовки для скачивания (RFC 5987)
    # Основной filename должен быть ASCII-совместимым, а полный UTF-8 — через filename*

    safe_filename = f"chapter_{chapter_id}.txt"
    full_filename = f"chapter_{chapter_id}_{project.name}_{chapter.title}.txt"
    encoded_full = "UTF-8''" + quote(full_filename, safe="")

    content_disposition = (
        f'attachment; filename="{safe_filename}"; filename*={encoded_full}'
    )

    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": content_disposition},
    )


@router.get("/chapters/{chapter_id}", response_model=ChapterRead)
def get_chapter(chapter_id: int, db: Session = Depends(get_db)) -> Chapter:
    """Получить главу по ID."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chapter(chapter_id: int, db: Session = Depends(get_db)):
    """Удалить главу."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    db.delete(chapter)
    db.commit()


@router.put("/chapters/{chapter_id}", response_model=ChapterRead)
def update_chapter(
    chapter_id: int, payload: ChapterUpdate, db: Session = Depends(get_db)
) -> Chapter:
    """Обновить поля главы (название, тексты)."""
    chapter = db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")

    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(chapter, field, value)

    db.commit()
    db.refresh(chapter)
    return chapter


# API для создания общего саммари проекта
@router.post("/{project_id}/generate-summary")
def generate_project_summary(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Создать общее саммари проекта на основе всех глав."""
    # Проверяем, что проект существует
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Получаем все главы проекта с саммари
    chapters = (
        db.query(Chapter)
        .filter(Chapter.project_id == project_id, Chapter.summary.isnot(None))
        .order_by(Chapter.id)
        .all()
    )

    if not chapters:
        raise HTTPException(
            status_code=400,
            detail="No chapters with summaries found. Please analyze chapters first.",
        )

    try:
        # Подготавливаем данные для создания саммари
        chapters_data = [
            {
                "title": chapter.title,
                "summary": chapter.summary,
                "original_text": chapter.original_text,
            }
            for chapter in chapters
        ]

        # Создаем общее саммари
        project_summary = context_summarizer.create_project_summary(chapters_data)

        return {
            "project_id": project_id,
            "summary": project_summary,
            "chapters_used": len(chapters),
            "message": "Project summary generated successfully",
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to generate project summary: {str(e)}"
        )


# ──────────────────────────────────────────────
# Project Gemini Settings (model/thinking overrides)
# ──────────────────────────────────────────────


@router.get("/{project_id}/settings")
def get_project_settings(project_id: int, db: Session = Depends(get_db)) -> dict:
    """Получить настройки модели и thinking для проекта."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.core.config import settings as app_settings

    return {
        "project_id": project_id,
        "overrides": {
            "model_extraction": project.model_extraction,
            "model_translation": project.model_translation,
            "model_summarization": project.model_summarization,
            "thinking_extraction": project.thinking_extraction,
            "thinking_translation": project.thinking_translation,
            "source_language": project.source_language,
            "target_language": project.target_language,
            "embedding_threshold": project.embedding_threshold,
        },
        "effective": {
            "model_extraction": project.model_extraction
            or app_settings.GEMINI_MODEL_EXTRACTION,
            "model_translation": project.model_translation
            or app_settings.GEMINI_MODEL_TRANSLATION,
            "model_summarization": project.model_summarization
            or app_settings.GEMINI_MODEL_SUMMARIZATION,
            "thinking_extraction": project.thinking_extraction
            or app_settings.GEMINI_THINKING_EXTRACTION,
            "thinking_translation": project.thinking_translation
            or app_settings.GEMINI_THINKING_TRANSLATION,
            "source_language": project.source_language or "en",
            "target_language": project.target_language or "ru",
            "embedding_threshold": project.embedding_threshold
            or app_settings.EMBEDDING_SIMILARITY_THRESHOLD,
        },
    }


@router.patch("/{project_id}/settings")
def update_project_settings(
    project_id: int,
    settings_update: dict,
    db: Session = Depends(get_db),
) -> dict:
    """Обновить настройки модели и thinking для проекта. Передайте null для сброса к defaults."""
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    allowed_fields = {
        "model_extraction",
        "model_translation",
        "model_summarization",
        "thinking_extraction",
        "thinking_translation",
        "source_language",
        "target_language",
        "embedding_threshold",
    }
    valid_thinking = {"minimal", "low", "medium", "high", None}

    for field, value in settings_update.items():
        if field not in allowed_fields:
            raise HTTPException(status_code=400, detail=f"Unknown setting: {field}")
        if (
            field.startswith("thinking_")
            and value is not None
            and value not in valid_thinking
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid thinking level: {value}. Use: minimal/low/medium/high",
            )
        setattr(project, field, value)

    db.commit()
    db.refresh(project)

    return get_project_settings(project_id, db)


@router.get("/models/available")
def get_available_models() -> dict:
    """Возвращает белый список моделей для UI."""
    from app.core.config import settings as app_settings

    return {
        "generation_models": [
            {
                "id": "gemini-3-flash-preview",
                "name": "Gemini 3 Flash Preview",
                "thinking": True,
                "tier": "flash",
            },
            {
                "id": "gemini-3.1-flash-lite-preview",
                "name": "Gemini 3.1 Flash Lite Preview",
                "thinking": True,
                "tier": "lite",
            },
            {
                "id": "gemini-2.5-flash",
                "name": "Gemini 2.5 Flash",
                "thinking": True,
                "tier": "flash",
            },
            {
                "id": "gemini-flash-latest",
                "name": "Gemini Flash Latest",
                "thinking": True,
                "tier": "flash",
            },
        ],
        "embedding_models": [
            {
                "id": "gemini-embedding-2-preview",
                "name": "Gemini Embedding 2 Preview",
                "dimensions": 768,
            },
        ],
        "thinking_levels": ["minimal", "low", "medium", "high"],
        "languages": {
            "source": [
                {"code": "zh", "name": "Chinese"},
                {"code": "ja", "name": "Japanese"},
                {"code": "ko", "name": "Korean"},
                {"code": "en", "name": "English"},
                {"code": "other", "name": "Other"},
            ],
            "target": [
                {"code": "ru", "name": "Russian"},
                {"code": "en", "name": "English"},
                {"code": "other", "name": "Other"},
            ],
        },
        "defaults": {
            "extraction": app_settings.GEMINI_MODEL_EXTRACTION,
            "translation": app_settings.GEMINI_MODEL_TRANSLATION,
            "summarization": app_settings.GEMINI_MODEL_SUMMARIZATION,
            "relationships": app_settings.GEMINI_MODEL_RELATIONSHIPS,
            "embedding_threshold": app_settings.EMBEDDING_SIMILARITY_THRESHOLD,
        },
    }


@router.post("/{project_id}/calibrate-threshold")
def calibrate_embedding_threshold(
    project_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Automatically calibrate embedding similarity threshold for a project.
    Computes pairwise cosine distances between approved terms with embeddings
    and sets the threshold at a percentile that separates related from unrelated terms.
    Requires at least 5 approved terms with embeddings.
    """
    import numpy as np

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Fetch approved terms with embeddings
    terms_with_embeddings = (
        db.query(GlossaryTerm)
        .filter(
            GlossaryTerm.project_id == project_id,
            GlossaryTerm.status == "approved",
            GlossaryTerm.embedding_vec.isnot(None),
        )
        .all()
    )

    if len(terms_with_embeddings) < 5:
        raise HTTPException(
            status_code=400,
            detail=f"Need at least 5 approved terms with embeddings for calibration. Found: {len(terms_with_embeddings)}",
        )

    # Compute pairwise cosine similarities
    vectors = []
    for term in terms_with_embeddings:
        vec = term.embedding_vec
        if hasattr(vec, "tolist"):
            vectors.append(vec)
        elif isinstance(vec, (list, tuple)):
            vectors.append(np.array(vec, dtype=np.float32))
        else:
            continue

    if len(vectors) < 5:
        raise HTTPException(
            status_code=400, detail="Not enough valid embedding vectors"
        )

    matrix = np.array(vectors, dtype=np.float32)
    # Normalize rows
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms

    # Cosine similarity matrix
    sim_matrix = matrix @ matrix.T

    # Extract upper triangle (exclude diagonal)
    n = sim_matrix.shape[0]
    upper_tri = []
    for i in range(n):
        for j in range(i + 1, n):
            upper_tri.append(float(sim_matrix[i, j]))

    if not upper_tri:
        raise HTTPException(
            status_code=400, detail="Could not compute pairwise similarities"
        )

    similarities = np.array(upper_tri)

    # Calculate threshold: 25th percentile of pairwise similarities
    threshold = float(np.percentile(similarities, 25))
    threshold = round(max(0.3, min(0.95, threshold)), 4)

    # Save to project
    project.embedding_threshold = threshold
    db.commit()
    db.refresh(project)

    return {
        "project_id": project_id,
        "calibrated_threshold": threshold,
        "terms_analyzed": len(vectors),
        "pairs_computed": len(upper_tri),
        "stats": {
            "min_similarity": round(float(similarities.min()), 4),
            "max_similarity": round(float(similarities.max()), 4),
            "mean_similarity": round(float(similarities.mean()), 4),
            "median_similarity": round(float(np.median(similarities)), 4),
            "p25_similarity": round(float(np.percentile(similarities, 25)), 4),
            "p75_similarity": round(float(np.percentile(similarities, 75)), 4),
        },
    }


@router.post("/{project_id}/backfill-embeddings")
def backfill_project_embeddings(
    project_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    DISPATCH embeddings generation tasks for all APPROVED glossary terms
    that do not currently have an embedding. Useful for legacy projects.
    """
    from app.tasks.embedding_tasks import generate_term_embedding_task

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    terms_missing_embeddings = (
        db.query(GlossaryTerm.id)
        .filter(
            GlossaryTerm.project_id == project_id,
            GlossaryTerm.status == "approved",
            GlossaryTerm.embedding_vec.is_(None)
        )
        .all()
    )

    term_ids = [t.id for t in terms_missing_embeddings]

    for tid in term_ids:
        generate_term_embedding_task.delay(tid)

    return {
        "project_id": project_id,
        "message": f"Successfully dispatched {len(term_ids)} embedding generation tasks to background.",
        "tasks_queued": len(term_ids),
    }
