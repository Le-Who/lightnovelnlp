from app.core.celery_app import celery_app

from app.tasks import nlp_tasks

if __name__ == "__main__":
    celery_app.start()
