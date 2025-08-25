from pydantic import BaseModel


class AuthBase(BaseModel):
    username: str
    password: str

    class Config:
        model_config = {
            "from_attributes": True
        }


class AuthLogin(AuthBase):
    pass


class AuthCookieLogin(AuthBase):
    pass
