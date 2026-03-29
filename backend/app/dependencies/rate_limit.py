"""
Rate limiting configuration using slowapi.

Protects sensitive endpoints from abuse:
- Login: 5 requests/minute per IP (prevents brute force password guessing)
- Upload: 10 requests/hour per user (prevents storage abuse)
- Chat: 30 requests/hour per user (prevents LLM cost abuse)

Uses Redis DB 4 as the backend storage for rate limit counters.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Create the limiter instance ───────────────────────────────────
# get_remote_address extracts the client's IP address from the request.
# This is used as the default key for rate limiting — each IP gets
# its own counter.

limiter = Limiter(key_func=get_remote_address)