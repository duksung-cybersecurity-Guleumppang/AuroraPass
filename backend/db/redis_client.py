import os
import json
import redis
from typing import Optional, Dict, Any

REDIS_URL = os.getenv("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "REDIS_URL is not set; please provide it via .env or environment variables."
    )

# Redis client instance with short socket timeouts to prevent readiness blocking
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
    socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT_SEC", "1.0")),
    socket_connect_timeout=float(os.getenv("REDIS_CONNECT_TIMEOUT_SEC", "1.0")),
)


def ping_redis() -> bool:
    """Test Redis connection"""
    try:
        return redis_client.ping()
    except Exception:
        return False


# Rate limiting functions
def increment_user_attempts(user_id: str, ttl_seconds: int = 3) -> int:
    """Increment user attempt count with TTL"""
    key = f"rl:{user_id}"
    current = redis_client.get(key)
    if current is None:
        redis_client.setex(key, ttl_seconds, 1)
        return 1
    else:
        return redis_client.incr(key)


def get_user_attempts(user_id: str) -> int:
    """Get current user attempt count"""
    key = f"rl:{user_id}"
    current = redis_client.get(key)
    return int(current) if current else 0


# CAPTCHA functions
def store_captcha(captcha_id: str, answer: str, ttl_minutes: int = 5) -> None:
    """Store CAPTCHA answer with TTL"""
    key = f"captcha:{captcha_id}"
    redis_client.setex(key, ttl_minutes * 60, answer)


def verify_captcha_redis(captcha_id: str, user_input: str) -> bool:
    """Verify CAPTCHA answer from Redis"""
    key = f"captcha:{captcha_id}"
    stored_answer = redis_client.get(key)
    if stored_answer and stored_answer.lower() == user_input.lower():
        redis_client.delete(key)  # One-time use
        return True
    return False


# Unlock functions
def grant_captcha_unlock(user_id: str, ttl_seconds: int = 30) -> None:
    """Grant temporary unlock after CAPTCHA success"""
    key = f"unlock:{user_id}"
    redis_client.setex(key, ttl_seconds, "1")


def check_captcha_unlock(user_id: str) -> bool:
    """Check if user has temporary unlock"""
    key = f"unlock:{user_id}"
    return redis_client.exists(key) > 0


def consume_captcha_unlock(user_id: str) -> bool:
    """Consume one-time unlock"""
    key = f"unlock:{user_id}"
    return redis_client.delete(key) > 0


# Idempotency helpers
def get_idempotent_payload(key: str) -> Optional[Dict[str, Any]]:
    """Get cached idempotent response payload by key."""
    raw = redis_client.get(f"idemp:{key}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_idempotent_payload(key: str, payload: Dict[str, Any], ttl_seconds: int = 30) -> None:
    """Cache idempotent response payload by key with TTL."""
    redis_client.setex(f"idemp:{key}", ttl_seconds, json.dumps(payload, ensure_ascii=False))


# Last response helpers (per fingerprint) to absorb quick duplicates without re-consumption
def get_last_generate_payload(fingerprint: str) -> Optional[Dict[str, Any]]:
    raw = redis_client.get(f"lastgen:{fingerprint}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_last_generate_payload(fingerprint: str, payload: Dict[str, Any], ttl_seconds: int = 5) -> None:
    redis_client.setex(f"lastgen:{fingerprint}", ttl_seconds, json.dumps(payload, ensure_ascii=False))
