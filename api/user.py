from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.depends.authorization import get_current_active_user
from core.exceptions import make_response_object
from database.database import get_async_session
from models import User
from services.user_service import UserService

router = APIRouter()

@router.get("/me")
async def get_me(session: AsyncSession = Depends(get_async_session), user: User = Depends(get_current_active_user)):
    user_service = UserService(session=session)
    user = await user_service.get_one_by_id(user_id=user.id)
    data = user.dict()
    return make_response_object(data=data)