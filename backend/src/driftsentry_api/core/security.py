import hashlib
import hmac
import secrets

KEY_PREFIX = "ds_live_"
VISIBLE_PREFIX_LENGTH = 16


def hash_ingestion_key(key: str, pepper: str) -> str:
    """Create a deterministic HMAC digest without storing the raw API key."""

    return hmac.new(pepper.encode(), key.encode(), hashlib.sha256).hexdigest()


def generate_ingestion_key(pepper: str) -> tuple[str, str, str]:
    """Return raw key, visible prefix, and stored digest."""

    raw_key = f"{KEY_PREFIX}{secrets.token_urlsafe(32)}"
    visible_prefix = raw_key[:VISIBLE_PREFIX_LENGTH]
    digest = hash_ingestion_key(raw_key, pepper)
    return raw_key, visible_prefix, digest


def verify_ingestion_key(candidate: str, expected_digest: str, pepper: str) -> bool:
    """Compare key digests in constant time."""

    candidate_digest = hash_ingestion_key(candidate, pepper)
    return hmac.compare_digest(candidate_digest, expected_digest)
