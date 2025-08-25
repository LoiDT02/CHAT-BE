from datetime import date, datetime
from sqlalchemy.orm import DeclarativeBase

from utils.convert_util import convert_to_DMY_str


class Base(DeclarativeBase):
    def to_dict(self, un_selects=None):
        result = {}
        for column in self.__table__.columns:
            if not un_selects or column.name not in un_selects:
                result[column.name] = getattr(self, column.name)
                if isinstance(result[column.name], date) or isinstance(result[column.name], datetime):
                    result[column.name] = convert_to_DMY_str(result[column.name])
        return result
