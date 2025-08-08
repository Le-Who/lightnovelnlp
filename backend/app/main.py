from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.api.projects import router as projects_router
from app.api.glossary import router as glossary_router
from app.api.processing import router as processing_router
from app.api.translation import router as translation_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Ranobe Translator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects_router, prefix="/projects", tags=["projects"])
app.include_router(glossary_router, prefix="/glossary", tags=["glossary"])
app.include_router(processing_router, prefix="/processing", tags=["processing"])
app.include_router(translation_router, prefix="/translation", tags=["translation"])
