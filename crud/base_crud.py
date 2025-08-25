from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from pydantic import BaseModel
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, RelationshipProperty, selectinload

from constant import AppStatus
from core import error_exception_handler

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]) -> None:
        self._model = model

    def _build_condition(self, key, value):
        if '__' in key:
            # Split the key into relationship and attribute parts
            relationship_key, attribute_key = key.split('__', 1)

            if hasattr(self._model, relationship_key):
                relationship_attr = getattr(self._model, relationship_key)
                if isinstance(relationship_attr, InstrumentedAttribute) and isinstance(relationship_attr.property,
                                                                                       RelationshipProperty):
                    related_model = relationship_attr.prop.mapper.class_
                    if hasattr(related_model, attribute_key):
                        condition = getattr(related_model, attribute_key) == value
                        if relationship_attr.property.uselist:
                            return relationship_attr.any(condition)
                        return relationship_attr.has(condition)
                    else:
                        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_DATA,
                                                      description=f"Trường '{attribute_key}' không tồn tại ở bảng liên quan.")
                else:
                    raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_DATA,
                                                  description=f"'{relationship_key}' không phải là một mối quan hệ hợp lệ.")
            else:
                raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_DATA,
                                              description=f"Trường '{relationship_key}' không tồn tại ở bảng này.")
        else:
            # Single part key, directly on the model
            if hasattr(self._model, key):
                return getattr(self._model, key) == value

        raise error_exception_handler(app_status=AppStatus.ERROR_400_INVALID_DATA,
                                      description=f"Trường '{key}' không tồn tại ở bảng này và các bảng liên quan.")

    def convert_filter_rpn_into_condition(self, rpn_list):
        stack = []
        for item in rpn_list:
            if item == '|':  # OR Operator
                right = stack.pop()
                left = stack.pop()
                result = or_(left, right)
            elif item == '&':  # AND Operator
                right = stack.pop()
                left = stack.pop()
                result = and_(left, right)
            else:  # Operand
                condition = {k: v for k, v in item.items()}  # Convert to dict if not already
                key = list(condition.keys())[0]
                value = condition[key]
                result = self._build_condition(key, value)
            stack.append(result)

        return stack.pop()

    def _apply_lazy_loading(self, query, relationships):
        if relationships:

            for field in relationships:
                fields = field.split(".")
                relation_attr = getattr(self._model, fields[0], None)

                if not relation_attr:
                    raise AttributeError(f"Model '{self._model.__name__}' has no field '{fields[0]}'")
                load_option = selectinload(relation_attr)
                for sub_field in fields[1:]:
                    sub_relation = getattr(relation_attr.property.mapper.class_, sub_field, None)
                    if not sub_relation:
                        raise AttributeError(f"Model '{relation_attr.property.mapper.class_.__name__}' has no field '{sub_field}'")
                    load_option = load_option.selectinload(sub_relation)
                    relation_attr = sub_relation
                query = query.options(load_option)

        return query

    async def create(
            self, session: AsyncSession, obj_in: CreateSchemaType
    ) -> ModelType:
        db_obj = self._model(**obj_in.dict())
        session.add(db_obj)
        await session.commit()
        return db_obj

    async def create_bulk(
            self, session: AsyncSession, objs_in: List[CreateSchemaType]
    ) -> List[ModelType]:
        db_objs = [self._model(**obj_in.dict()) for obj_in in objs_in]
        session.add_all(db_objs)
        await session.commit()
        return db_objs

    async def get(self, session: AsyncSession, *args, relationships: Optional[List[str]] = None, **kwargs) -> Optional[ModelType]:
        result = await session.execute(
            self._apply_lazy_loading(select(self._model), relationships).filter(*args).filter_by(**kwargs)
        )
        return result.scalars().first()

    async def get_multi(
            self, session: AsyncSession, *args, relationships: Optional[List[str]] = None, offset: int = 0, limit: int = 100, **kwargs
    ) -> List[ModelType]:
        query = self._apply_lazy_loading(select(self._model), relationships)

        if "filter_rpn" in kwargs:
            if len(kwargs["filter_rpn"]):
                condition = self.convert_filter_rpn_into_condition(kwargs["filter_rpn"])
                query = query.filter(condition)
            del kwargs["filter_rpn"]

        query = query.filter(*args).filter_by(**kwargs).offset(offset).limit(limit)

        result = await session.execute(query)

        return result.scalars().all()

    async def get_all(
            self, session: AsyncSession, *args, relationships: Optional[List[str]] = None, **kwargs
    ) -> List[ModelType]:
        query = self._apply_lazy_loading(select(self._model), relationships)

        if "filter_rpn" in kwargs:
            if len(kwargs["filter_rpn"]):
                condition = self.convert_filter_rpn_into_condition(kwargs["filter_rpn"])
                query = query.filter(condition)
            del kwargs["filter_rpn"]

        query = query.filter(*args).filter_by(**kwargs)

        result = await session.execute(query)

        return result.scalars().all()

    async def count_all(
            self, session: AsyncSession, *args, **kwargs
    ) -> int:
        query = select(func.count()).select_from(self._model)

        if "filter_rpn" in kwargs:
            if len(kwargs["filter_rpn"]):
                condition = self.convert_filter_rpn_into_condition(kwargs["filter_rpn"])
                query = query.filter(condition)
            del kwargs["filter_rpn"]

        query = query.filter(*args).filter_by(**kwargs)

        result = await session.execute(query)

        return result.scalar_one()

    async def update(
            self,
            session: AsyncSession,
            *,
            obj_in: Union[UpdateSchemaType, Dict[str, Any]],
            db_obj: Optional[ModelType] = None,
            **kwargs
    ) -> Optional[ModelType]:
        db_obj = db_obj or await self.get(session, **kwargs)
        if db_obj is not None:
            obj_data = db_obj.to_dict()
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data and update_data[field] is not None:
                    setattr(db_obj, field, update_data[field])
            session.add(db_obj)
            await session.commit()
        return db_obj

    async def update_bulk(
            self,
            session: AsyncSession,
            objs_in: List[UpdateSchemaType],
            db_objs: Optional[List[ModelType]] = None,
    ) -> List[ModelType]:
        db_objs = db_objs or await self.get_multi(session)
        if len(objs_in) != len(db_objs):
            raise ValueError("Input and existing objects count mismatch")

        for i, db_obj in enumerate(db_objs):
            obj_data = db_obj.to_dict()
            update_data = objs_in[i].dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])

        await session.commit()
        return db_objs

    async def delete(
            self, session: AsyncSession, *args, db_obj: Optional[ModelType] = None, **kwargs
    ) -> ModelType:
        db_obj = db_obj or await self.get(session, *args, **kwargs)
        await session.delete(db_obj)
        await session.commit()
        return db_obj

    async def delete_bulk(self, session: AsyncSession, db_objs: Optional[List[ModelType]] = None):
        for obj in db_objs:
            await session.delete(obj)  # Assuming self.delete is your method for deleting individual objects.
        await session.commit()
