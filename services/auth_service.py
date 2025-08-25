import logging

from sqlalchemy.ext.asyncio import AsyncSession

from api.depends.authorization import create_access_token, create_refresh_token
from constant import AppStatus
from core import error_exception_handler
from crud.user_crud import user_crud
from models.user import User
from schemas import AuthLogin, UserUpdate
from utils.hash_util import verify_password

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