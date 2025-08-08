from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db import Base, engine
from app.api.projects import router as projects_router

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
