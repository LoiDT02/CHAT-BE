from fastapi import Depends, APIRouter, Response, Request, HTTPException

from api.depends.authorization import get_current_active_user, create_access_token, create_refresh_token
from constant import ACCESS_TOKEN_EXPIRES_IN_SECONDS, REFRESH_TOKEN_EXPIRES_IN_SECONDS
from core import settings
from core.exceptions import make_response_object
from crud import user_crud
from database.database import get_async_session
from models import User
from schemas import AuthLogin, UserCreate, UserUpdate
from services.auth_service import AuthService
from sqlalchemy.ext.asyncio import AsyncSession
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from fastapi.responses import RedirectResponse
router = APIRouter()
config = Config(environ={
    "GOOGLE_CLIENT_ID": settings.GOOGLE_CLIENT_ID,
    "GOOGLE_CLIENT_SECRET": settings.GOOGLE_CLIENT_SECRET,
})
oauth = OAuth(config)
oauth.register(
    name='google',
    client_id=config("GOOGLE_CLIENT_ID"),
    client_secret=config("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

@router.get("/google")
async def login_via_google(request: Request):
    redirect_uri = "https://api.codelearnit.io.vn/auth/google/callback"
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/google/callback")
async def google_callback(request: Request, session=Depends(get_async_session)):
    try:
        token = await oauth.google.authorize_access_token(request)
        print("👉 Token:", token)
    except Exception as e:
        print("❌ Lỗi authorize_access_token:", str(e))
        raise HTTPException(status_code=400, detail="Google auth failed")

    user_info = token.get("userinfo")
    print("👉 User info:", user_info)

    if not user_info:
        raise HTTPException(status_code=400, detail="Google login failed")

    email = user_info["email"]

    user = await user_crud.get(session, User.email == email)
    if not user:
        user = await user_crud.create(
            session=session,
            obj_in=UserCreate(
                username=email.split("@")[0],
                email=email,
                hashed_password=None,
                is_active=True
            )
        )

    data = {"user_id": user.id, "username": user.username}
    access_token = create_access_token(data=data)
    refresh_token = create_refresh_token(data=data)

    await user_crud.update(
        session=session,
        obj_in=UserUpdate(access_token=access_token, refresh_token=refresh_token),
        db_obj=user
    )

    redirect_response = RedirectResponse(url="https://codelearnit.io.vn")
    redirect_response.set_cookie(
        key="access_token", value=access_token,
        max_age=ACCESS_TOKEN_EXPIRES_IN_SECONDS,
        httponly=True, secure=True, samesite="none",
        domain=".codelearnit.io.vn"
    )
    redirect_response.set_cookie(
        key="refresh_token", value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRES_IN_SECONDS,
        httponly=True, secure=True, samesite="none",
        domain=".codelearnit.io.vn"
    )

    return redirect_response


@router.post('/login')
async def login(auth_data: AuthLogin, response: Response, session: AsyncSession = Depends(get_async_session)):
    auth_service = AuthService(session=session)
    auth_response = await auth_service.login(auth_data=auth_data)
    access_token = auth_response.get("access_token")
    refresh_token = auth_response.get("refresh_token")
    response.set_cookie(key="access_token", value=access_token, max_age=ACCESS_TOKEN_EXPIRES_IN_SECONDS,
                        httponly=True, secure=True,samesite="none",domain=settings.COOKIE_DOMAIN)
    response.set_cookie(key="refresh_token", value=refresh_token, max_age=REFRESH_TOKEN_EXPIRES_IN_SECONDS,
                        httponly=True, secure=True,samesite="none",domain=settings.COOKIE_DOMAIN)
    return make_response_object("Đăng nhập thành công")

@router.get('/cookie-jwt/logout')
async def logout_cookie(response: Response, user: User = Depends(get_current_active_user),
                        session: AsyncSession = Depends(get_async_session)):
    auth_service = AuthService(session=session)
    await auth_service.logout(user=user)
    response.delete_cookie(key="access_token", httponly=True, secure=True, samesite="none", domain=".codelearnit.io.vn")
    response.delete_cookie(key="refresh_token", httponly=True, secure=True, samesite="none", domain=".codelearnit.io.vn")
    return make_response_object("Đăng xuất thành công")

@router.post('/reset-password/{user_id}')
async def reset_password(user_id: int, session: AsyncSession = Depends(get_async_session),
                         user: User = Depends(get_current_active_user)):
    auth_service = AuthService(session=session)
    auth_response = await auth_service.reset_password(user_id=user_id)
    return make_response_object({"user_id": auth_response[0], "new_password": auth_response[1]})

@router.post('/cookie-jwt/refresh-token')
async def refresh_token_cookie(request: Request, response: Response,
                               session: AsyncSession = Depends(get_async_session)):
    auth_service = AuthService(session=session)
    auth_response = await auth_service.refresh_token_cookie(request=request)
    access_token = auth_response.get("access_token")
    refresh_token = auth_response.get("refresh_token")
    max_age = auth_response.get("max_age")
    response.set_cookie(key="access_token", value=access_token,
                        max_age=ACCESS_TOKEN_EXPIRES_IN_SECONDS, httponly=True, secure=True, samesite="none")
    response.set_cookie(key="refresh_token", value=refresh_token, max_age=max_age, httponly=True, secure=True, samesite="none")
    return make_response_object("Làm mới token thành công")