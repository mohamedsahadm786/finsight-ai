from backend.tasks.celery_app import celery_app
from backend.tasks.document_tasks import process_document

__all__ = ["celery_app", "process_document"]