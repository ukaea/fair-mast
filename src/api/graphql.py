from typing import List, Generic, TypeVar, Optional, get_type_hints
from dataclasses import asdict, make_dataclass, field

import strawberry
from sqlmodel import Session
from strawberry.extensions import Extension

from . import utils, models
from .database import engine
from .models import ShotModel, SignalModel, ShotSignalLink

T = TypeVar("T")


@strawberry.input()
class ComparatorFilter(Generic[T]):
    eq: Optional[T] = None
    neq: Optional[T] = None
    gt: Optional[T] = None
    lt: Optional[T] = None
    gte: Optional[T] = None
    lte: Optional[T] = None
    isNull: Optional[bool] = None
    contains: Optional[str] = None


def make_where_filter(type_):
    type_name = type_.__name__
    type_name = type_name.replace("Model", "")
    filter_name = f"{type_name}WhereFilter"

    type_hints = get_type_hints(type_)
    fields = []
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            field_type = utils.unwrap_optional(field_type)
            if not utils.is_list(field_type):
                fields.append(
                    (name, Optional[ComparatorFilter[field_type]], field(default=None))
                )

    cls_ = make_dataclass(
        filter_name, fields=fields, namespace={"__module__": __name__}
    )
    cls_ = strawberry.input(
        cls_, description="A where filter for selecting a subset of rows"
    )
    return cls_


ShotWhereFilter = make_where_filter(models.ShotModel)
SignalWhereFilter = make_where_filter(models.SignalModel)


def do_where(model_cls, query, where):
    if where is None:
        return query

    where = asdict(where)
    for name, filters in where.items():
        if filters is not None:
            for op_name, value in filters.items():
                if value is not None:
                    op = comparator_map[op_name]
                    query = query.filter(op(getattr(model_cls, name), value))
    return query


def get_shots(info, where, limit):
    db = info.context["db"]
    query = db.query(models.ShotModel)
    query = do_where(ShotModel, query, where)
    query = query.order_by(ShotModel.shot_id.desc())
    query = query.limit(limit) if limit is not None else query
    rows = query.all()
    return rows


class SQLAlchemySession(Extension):
    def on_request_start(self):
        self.execution_context.context["db"] = Session(
            autocommit=False, autoflush=False, bind=engine, future=True
        )

    def on_request_end(self):
        self.execution_context.context["db"].close()


@strawberry.experimental.pydantic.type(
    model=ShotSignalLink,
    all_fields=True,
    description="Linking table between shot and signal metadata",
)
class ShotSignalLink:
    pass


@strawberry.experimental.pydantic.type(
    model=ShotModel,
    all_fields=True,
    description="Shot objects contain metadata about a single experimental shot including CPF data values.",
)
class Shot:
    @strawberry.field(
        description="Get information about signals from diagnostic equipment."
    )
    def signals(
        self,
        info,
        where: Optional[SignalWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[strawberry.LazyType["Signal", __module__]]:
        return get_shots(info, where, limit)


@strawberry.experimental.pydantic.type(
    model=SignalModel,
    all_fields=True,
    description="Signal objects contain metadata about a signal from a diagnostic.",
)
class Signal:
    @strawberry.field(description="Get information about shots.")
    def shots(
        self,
        info,
        where: Optional[ShotWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Shot]:
        return get_shots(info, where, limit)


comparator_map = {
    "contains": lambda column, value: column.contains(value),
    "isNull": lambda column, value: (column is None) == value,  # XOR
    "eq": lambda column, value: column == value,
    "neq": lambda column, value: column != value,
    "lt": lambda column, value: column < value,
    "gt": lambda column, value: column > value,
    "lte": lambda column, value: column <= value,
    "gte": lambda column, value: column >= value,
}


@strawberry.type
class Query:
    @strawberry.field(description="Get information about shots.")
    def shots(
        self,
        info,
        where: Optional[ShotWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Shot]:
        return get_shots(info, where, limit)

    @strawberry.field(
        description="Get information about signals from diagnostic equipment"
    )
    def signals(
        self,
        info,
        where: Optional[SignalWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Signal]:
        db = info.context["db"]
        query = db.query(models.SignalModel)
        query = do_where(SignalModel, query, where)
        query = query.order_by(SignalModel.name)
        query = query.limit(limit) if limit is not None else query
        rows = query.all()
        return rows


schema = strawberry.Schema(query=Query, extensions=[SQLAlchemySession])
