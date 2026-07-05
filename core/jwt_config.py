from datetime import datetime, timedelta
from jose import jwt
from jose import JWTError

from core.config import SECRET_KEY

ALGORITHM = "HS256"


def create_token(user_id: int, expires_delta: timedelta):
    payload = {
        "sub": str(user_id),
        "exp": datetime.utcnow() + expires_delta
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def create_access_token(user_id: int):
    return create_token(user_id, timedelta(days=1))


def create_refresh_token(user_id: int):
    return create_token(user_id, timedelta(days=30))


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
