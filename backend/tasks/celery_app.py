from celery import Celery
from backend.app.config import get_settings

settings = get_settings()

# ============================================================
# Celery Application
# ============================================================
# Broker: Redis DB 0 (task queue)
# Backend: Redis DB 0 (task result storage)
# ============================================================

celery_app = Celery(
    "finsight_worker",
    broker=settings.redis_url(db=0),
    backend=settings.redis_url(db=0),
)

# ---- Serialization ----
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]

# ---- Timezone ----
celery_app.conf.timezone = "UTC"
celery_app.conf.enable_utc = True

# ---- Task behavior ----
celery_app.conf.task_acks_late = True            # Acknowledge AFTER task completes
celery_app.conf.worker_prefetch_multiplier = 1   # Only fetch 1 task at a time
celery_app.conf.task_track_started = True         # Track "STARTED" state

# ---- Task retry defaults ----
celery_app.conf.task_default_retry_delay = 30
celery_app.conf.task_max_retries = 3

# ---- Result expiry ----
celery_app.conf.result_expires = 86400            # 24 hours
celery_app.conf.broker_connection_retry_on_startup = True

# ---- Auto-discover tasks ----
celery_app.autodiscover_tasks(["backend.tasks"])