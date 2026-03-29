"""
Database dependency re-export.

This makes it cleaner to import the database session in API routers:
    from backend.app.dependencies.database import get_db

Instead of:
    from backend.app.database.session import get_db
"""

from backend.app.database.session import get_db

__all__ = ["get_db"]