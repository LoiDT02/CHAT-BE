import logging

from sqlalchemy.ext.asyncio import AsyncSession

from constant import AppStatus
from core import error_exception_handler
from crud import user_crud
from models import User

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_one_by_id(self, user_id: int):
        user = await user_crud.get(self.session, User.id == user_id)
        if user is None:
            logger.error(AppStatus.ERROR_404_USER_NOT_FOUND.message,
                         exc_info=ValueError(AppStatus.ERROR_404_USER_NOT_FOUND))
            raise error_exception_handler(app_status=AppStatus.ERROR_404_USER_NOT_FOUND)
        return user