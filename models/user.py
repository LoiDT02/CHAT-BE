from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    def dict(self):
        result = self.to_dict(un_selects=["hashed_password", "access_token", "refresh_token"])
        return result
