from datetime import datetime, timedelta
from jose import jwt
from jose import JWTError

from core.config import SECRET_KEY

ALGORITHM = "HS256"


def create_token(user_id: int, expires_delta: timedelta, role: str, token_type: str):
    payload = {
        "sub": str(user_id),
        "role": role,
        "token_type": token_type,
        "exp": datetime.utcnow() + expires_delta,
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_access_token(user_id: int, role: str = "parent"):
    return create_token(user_id, timedelta(days=7), role, "access")


def create_refresh_token(user_id: int, role: str = "parent"):
    return create_token(user_id, timedelta(days=30), role, "refresh")


def decode_token(token: str):
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM],
    )


def get_token_subject(token: str):
    try:
        payload = decode_token(token)
        return int(payload.get("sub"))
    except (JWTError, TypeError, ValueError):
        return None


def get_token_payload(token: str):
    try:
        return decode_token(token)
    except JWTError:
        return None


def get_auth_context(token: str):
    payload = get_token_payload(token)
    if not payload:
        return None

    return {
        "user_id": payload.get("sub"),
        "role": payload.get("role"),
    }
