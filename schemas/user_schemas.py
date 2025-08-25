import logging
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class UserBase(BaseModel):
    username: str
    is_active: bool

    class Config:
        model_config = {
            "from_attributes": True
        }


class UserCreate(UserBase):
    hashed_password: str
    is_active: Optional[bool] = True


class UserUpdate(UserBase):
    username: Optional[str] = None
    is_active: Optional[bool] = None
    hashed_password: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None