import redis.asyncio as aioredis

from backend.app.config import get_settings

settings = get_settings()


def get_redis(db: int = 0) -> aioredis.Redis:
    """Get a Redis connection for a specific logical database.

    DB 0 = Celery task queue (managed by Celery)
    DB 1 = Dead letter queue (failed jobs after 3 retries)
    DB 2 = Application cache (API response caching)
    DB 3 = JWT blacklist (revoked access tokens)
    DB 4 = Rate limiting counters
    """
    return aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=db,
        decode_responses=True,
    )


# Pre-configured instances for common use
redis_cache = get_redis(db=2)
redis_blacklist = get_redis(db=3)
redis_rate_limit = get_redis(db=4)