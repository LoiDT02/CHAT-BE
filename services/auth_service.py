import logging
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from constant import AppStatus
from core import error_exception_handler
from crud.user_crud import user_crud
from models.user import User
from fastapi import Request, HTTPException
from schemas import AuthLogin, UserUpdate
from utils.hash_util import verify_password, hash_password
from api.depends.authorization import create_access_token, create_refresh_token, verify_refresh_token
logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def login(self, auth_data: AuthLogin):
        user = await user_crud.get(self.session, User.username == auth_data.username)

        if user is None:
            logger.error(AppStatus.ERROR_404_USER_NOT_FOUND.message,
                         exc_info=ValueError(AppStatus.ERROR_404_USER_NOT_FOUND))
            raise error_exception_handler(app_status=AppStatus.ERROR_404_USER_NOT_FOUND)

        if not user.is_active:
            logger.error(AppStatus.HTTP_401_USER_NOT_ACTIVE.message,
                         exc_info=ValueError(AppStatus.HTTP_401_USER_NOT_ACTIVE))

            raise error_exception_handler(app_status=AppStatus.HTTP_401_USER_NOT_ACTIVE)

        if not user.hashed_password:
            raise error_exception_handler(app_status=AppStatus.HTTP_402_USER_NOT_ACTIVE_WITH_PASSWORD)

        if not verify_password(password=auth_data.password, hashed_password=user.hashed_password):
            logger.error(AppStatus.ERROR_400_INVALID_USERNAME_PASSWORD.message,
                         exc_info=ValueError(AppStatus.ERROR_400_INVALID_USERNAME_PASSWORD))
            raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_USERNAME_PASSWORD)

        data = {"user_id": user.id, "username": user.username}

        access_token = create_access_token(data=data)
        refresh_token = create_refresh_token(data=data)

        await user_crud.update(session=self.session,
                               obj_in=UserUpdate(access_token=access_token, refresh_token=refresh_token), db_obj=user)
        return {"access_token": access_token, "refresh_token": refresh_token}

    async def logout(self, user):
        logger.info(f"logout called by {user.username}.")
        access_token = ""
        refresh_token = ""
        await user_crud.update(session=self.session, obj_in=UserUpdate(access_token=access_token,
                                                                       refresh_token=refresh_token), db_obj=user)
        logger.info(f"logout called successfully with access_token:{access_token}, refresh_token:{refresh_token}")
        return {"access_token": access_token, "refresh_token": refresh_token}


    async def refresh_token_cookie(self, request: Request):
        logger.info(f"Service: refresh_token_cookie called.")
        refresh_token = request.cookies.get("refresh_token")
        (decoded_token, user) = await verify_refresh_token(token=refresh_token, session=self.session)
        refresh_token_expire = decoded_token.get("exp", 0)
        access_data = {
            "user_id": decoded_token.get("user_id"),
            "username": decoded_token.get("username")
        }
        access_token = create_access_token(data=access_data)
        refresh_token = create_refresh_token(data=access_data, expired_at=refresh_token_expire)
        await user_crud.update(session=self.session,
                               obj_in=UserUpdate(access_token=access_token, refresh_token=refresh_token), db_obj=user)

        time_difference = datetime.utcfromtimestamp(refresh_token_expire) - datetime.utcnow()
        time_difference_seconds = int(time_difference.total_seconds())
        logger.info(f"Service: refresh_token_cookie called successfully, access_token:{access_token},"
                    f" refresh_token:{refresh_token}, max_age:{time_difference_seconds}")
        return {"access_token": access_token, "refresh_token": refresh_token, "max_age": time_difference_seconds}

    async def reset_password(self, user_id: int):
        logger.info(f"user_id: {user_id} reset_password called.")
        user = await user_crud.get(self.session, User.id == user_id)
        if user is None:
            logger.error(AppStatus.ERROR_404_USER_NOT_FOUND.message,
                         exc_info=ValueError(AppStatus.ERROR_404_USER_NOT_FOUND))
            raise error_exception_handler(app_status=AppStatus.ERROR_404_USER_NOT_FOUND)
        new_password = user.username
        hashed_password = hash_password(new_password)
        await user_crud.update_password(session=self.session, hashed_password=hashed_password, user=user)

        logger.info(
            f"user_id: {user_id} reset_password called successfully, user_id:{user_id}, password:{new_password}")
        return user_id, new_password