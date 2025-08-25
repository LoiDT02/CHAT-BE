from fastapi import Depends, APIRouter, Response

from constant import ACCESS_TOKEN_EXPIRES_IN_SECONDS, REFRESH_TOKEN_EXPIRES_IN_SECONDS
from core.exceptions import make_response_object
from database.database import get_async_session
from schemas import AuthLogin
from services import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()

@router.post('/login')
async def login(auth_data: AuthLogin, response: Response, session: AsyncSession = Depends(get_async_session)):
    auth_service = AuthService(session=session)
    auth_response = await auth_service.login(auth_data=auth_data)
    access_token = auth_response.get("access_token")
    refresh_token = auth_response.get("refresh_token")
    print(access_token, refresh_token)
    response.set_cookie(key="access_token", value=access_token, max_age=ACCESS_TOKEN_EXPIRES_IN_SECONDS,
                        httponly=True, secure=True,samesite="none")
    response.set_cookie(key="refresh_token", value=refresh_token, max_age=REFRESH_TOKEN_EXPIRES_IN_SECONDS,
                        httponly=True, secure=True,samesite="none")
    return make_response_object("Đăng nhập thành công")