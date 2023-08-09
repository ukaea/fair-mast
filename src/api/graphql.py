from typing import List, Generic, TypeVar, Optional, get_type_hints, get_origin
from dataclasses import dataclass, asdict, make_dataclass, field

import strawberry
from sqlmodel import Session
from strawberry.extensions import Extension

from .schema_generation import (
    unwrap_optional,
    create_array_relationship_resolver,
    create_generation_context,
    create_query_root,
)
from . import crud
from .database import engine
from .models import ShotModel


class SQLAlchemySession(Extension):
    def on_request_start(self):
        self.execution_context.context["db"] = Session(
            autocommit=False, autoflush=False, bind=engine, future=True
        )

    def on_request_end(self):
        self.execution_context.context["db"].close()


@strawberry.experimental.pydantic.type(model=ShotModel, all_fields=True)
class Shot:
    pass


comparator_map = {
    "isNull": lambda column, value: (column == None) == value,  # XOR
    "eq": lambda column, value: column == value,
    "neq": lambda column, value: column != value,
    "lt": lambda column, value: column < value,
    "gt": lambda column, value: column > value,
    "lte": lambda column, value: column <= value,
    "gte": lambda column, value: column >= value,
}

T = TypeVar("T")


@strawberry.input()
class ComparatorFilter(Generic[T]):
    isNull: Optional[bool] = None
    eq: Optional[T] = None
    neq: Optional[T] = None
    gt: Optional[T] = None
    lt: Optional[T] = None
    gte: Optional[T] = None
    lte: Optional[T] = None


def make_where_filter(type_):
    type_hints = get_type_hints(type_)
    fields = []
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            field_type = unwrap_optional(field_type)
            fields.append(
                (name, Optional[ComparatorFilter[field_type]], field(default=None))
            )

    cls_ = make_dataclass(
        "ShotWhereFilter", fields=fields, namespace={"__module__": __name__}
    )
    return strawberry.input(cls_)


def do_where(model_cls, query, where):
    where = asdict(where)
    for name, filters in where.items():
        if filters is not None:
            for op_name, value in filters.items():
                if value is not None:
                    op = comparator_map[op_name]
                    query = query.filter(op(getattr(model_cls, name), value))
    return query


@strawberry.type
class Query:
    @strawberry.field()
    def shots(
        self, info, where: Optional[make_where_filter(ShotModel)] = None
    ) -> List[Shot]:
        db = info.context["db"]
        query = crud.get_shots_stream(db)
        query = do_where(ShotModel, query, where)
        query = query.order_by(ShotModel.shot_id.desc())
        rows = query.all()
        return rows


schema = strawberry.Schema(query=Query, extensions=[SQLAlchemySession])
