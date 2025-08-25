import logging
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from constant import AppStatus
from constant.auth_constants import ACCESS_TOKEN_EXPIRES_IN_SECONDS, REFRESH_TOKEN_EXPIRES_IN_SECONDS, JWT_ALGORITHM
from core import settings, error_exception_handler
from database import get_async_session
from services.user_service import UserService

logger = logging.getLogger(__name__)


def create_token(data: dict, token_type: str, expired_at=None):
    to_encode = data.copy()
    created_at = datetime.utcnow().timestamp()
    if token_type == "access":
        expired_at = datetime.utcnow() + timedelta(seconds=ACCESS_TOKEN_EXPIRES_IN_SECONDS)
    else:
        expired_at = datetime.utcfromtimestamp(expired_at) if expired_at is not None \
            else datetime.utcnow() + timedelta(seconds=REFRESH_TOKEN_EXPIRES_IN_SECONDS)
    to_encode.update({"token_type": token_type, "exp": expired_at, "created_at": created_at})

    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)

    return encoded_jwt


def create_access_token(data: dict):
    return create_token(data, token_type="access")


def create_refresh_token(data: dict, expired_at=None):
    return create_token(data, token_type="refresh", expired_at=expired_at)


async def verify_token(token: str, session: AsyncSession):
    if not token:
        logger.error(AppStatus.ERROR_400_INVALID_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_400_INVALID_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_TOKEN)

    try:
        decoded_token = jwt.decode(token,
                                   settings.JWT_SECRET,
                                   algorithms=JWT_ALGORITHM)
    except jwt.exceptions.ExpiredSignatureError:
        logger.error(AppStatus.ERROR_401_EXPIRED_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_401_EXPIRED_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_401_EXPIRED_TOKEN)
    except jwt.exceptions.InvalidSignatureError:
        logger.error(AppStatus.ERROR_400_INVALID_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_400_INVALID_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_TOKEN)
    except jwt.exceptions.DecodeError:
        logger.error(AppStatus.ERROR_400_INVALID_TOKEN.message, exc_info=ValueError(AppStatus.ERROR_400_INVALID_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_TOKEN)
    # check user existence
    user_id = decoded_token['user_id']
    user_service = UserService(session=session)
    user = await user_service.get_one_by_id(user_id=user_id)
    token_type = decoded_token['token_type']
    if (token_type == "access" and user.access_token != token) or (
            token_type == "refresh" and user.refresh_token != token):
        logger.error(AppStatus.ERROR_401_EXPIRED_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_401_EXPIRED_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_401_EXPIRED_TOKEN)
    if not user.is_active:
        logger.error(AppStatus.HTTP_401_USER_NOT_ACTIVE.message,
                     exc_info=ValueError(AppStatus.HTTP_401_USER_NOT_ACTIVE))

        raise error_exception_handler(app_status=AppStatus.HTTP_401_USER_NOT_ACTIVE)
    return decoded_token, user


async def verify_access_token(
        token: str,
        session: AsyncSession,
):
    (decoded_token, user) = await verify_token(token, session)
    if decoded_token['token_type'] != "access":
        logger.error(AppStatus.ERROR_400_INVALID_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_400_INVALID_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_TOKEN)
    return user


async def verify_refresh_token(
        token: str,
        session: AsyncSession,
):
    (decoded_token, user) = await verify_token(token, session)
    if decoded_token['token_type'] != "refresh":
        logger.error(AppStatus.ERROR_400_INVALID_TOKEN.message,
                     exc_info=ValueError(AppStatus.ERROR_400_INVALID_TOKEN))
        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_TOKEN)
    return decoded_token, user


async def get_current_active_user(
        request: Request,
        credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
        session: AsyncSession = Depends(get_async_session)
):
    token = None
    if request.cookies.get("access_token", None):
        token = request.cookies["access_token"]
    elif credentials:
        token = credentials.credentials
    print('token',token)
    user = await verify_access_token(token=token, session=session)
    return user