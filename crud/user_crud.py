from crud.base_crud import BaseCRUD
from models import User
from schemas import UserCreate, UserUpdate


class UserCRUD(BaseCRUD[User, UserCreate, UserUpdate]):
    pass

user_crud = UserCRUD(User)
