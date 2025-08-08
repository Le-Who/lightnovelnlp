from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import engine, Base
from app.api import projects, glossary, processing, translation, batch

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Light Novel NLP API", version="1.0.0")

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(glossary.router, prefix="/glossary", tags=["glossary"])
app.include_router(processing.router, prefix="/processing", tags=["processing"])
app.include_router(translation.router, prefix="/translation", tags=["translation"])
app.include_router(batch.router, prefix="/batch", tags=["batch"])


@app.get("/")
def read_root():
    return {"message": "Light Novel NLP API", "version": "1.0.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
