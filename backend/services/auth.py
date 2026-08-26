import hashlib
import hmac
import os
import base64
import time


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return base64.b64encode(salt + key).decode()


def verify_password(password: str, stored_hash: str) -> bool:
    decoded = base64.b64decode(stored_hash.encode())
    salt = decoded[:16]
    key = decoded[16:]
    new_key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return hmac.compare_digest(key, new_key)


def create_token(user_id: int) -> str:
    secret = os.getenv('SESSION_SECRET', 'dev-secret')
    payload = f"{user_id}:{int(time.time())}"
    sig = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return base64.b64encode(f"{payload}:{sig}".encode()).decode()


def verify_token(token: str) -> int | None:
    try:
        secret = os.getenv('SESSION_SECRET', 'dev-secret')
        decoded = base64.b64decode(token.encode()).decode()
        payload, sig = decoded.rsplit(':', 1)
        expected = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        user_id = int(payload.split(':')[0])
        return user_id
    except Exception:
        return None
