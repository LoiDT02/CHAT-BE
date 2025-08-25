from fastapi import APIRouter
from api import (auth_routes, ws_routes, user_routes)
main_router = APIRouter()
main_router.include_router(auth_routes, prefix="/auth", tags=["auth"])
main_router.include_router(ws_routes, prefix="/ws", tags=["ws"])
main_router.include_router(user_routes, prefix="/user", tags=["user"])