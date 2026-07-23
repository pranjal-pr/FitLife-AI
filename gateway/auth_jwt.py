"""
JWT Authentication for AI Fit Pro API Gateway.

Provides token generation, validation, and decorator-based route protection
that works alongside the existing Flask-Login session auth.
"""

import os
import jwt
import functools
from datetime import datetime, timezone, timedelta
from flask import request, g, jsonify, current_app

JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
REFRESH_TOKEN_EXPIRES = timedelta(days=7)

_DEFAULT_SECRET = 'dev-jwt-secret-change-in-production'


def _get_secret() -> str:
    return os.environ.get('JWT_SECRET_KEY', _DEFAULT_SECRET)


def generate_tokens(user_id: int) -> dict:
    now = datetime.now(timezone.utc)
    secret = _get_secret()

    access_payload = {
        'sub': str(user_id),
        'type': 'access',
        'iat': now,
        'exp': now + ACCESS_TOKEN_EXPIRES,
    }
    refresh_payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'iat': now,
        'exp': now + REFRESH_TOKEN_EXPIRES,
    }

    return {
        'access_token': jwt.encode(access_payload, secret, algorithm=JWT_ALGORITHM),
        'refresh_token': jwt.encode(refresh_payload, secret, algorithm=JWT_ALGORITHM),
    }


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, _get_secret(), algorithms=[JWT_ALGORITHM])
        payload['sub'] = int(payload['sub'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, KeyError):
        return None


def _extract_user_id_from_header() -> int | None:
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:]
    payload = decode_token(token)
    if payload and payload.get('type') == 'access':
        return payload.get('sub')
    return None


def jwt_required(fn):
    """Reject requests without a valid JWT access token."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        user_id = _extract_user_id_from_header()
        if user_id is None:
            return jsonify({'error': 'Authentication required'}), 401
        g.current_user_id = user_id
        return fn(*args, **kwargs)
    return wrapper


def jwt_optional(fn):
    """Allow unauthenticated requests but attach user_id when present."""
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user_id = _extract_user_id_from_header()
        return fn(*args, **kwargs)
    return wrapper
