from typing import List, Generic, TypeVar, Optional, get_type_hints, Annotated
from dataclasses import asdict, make_dataclass, field

from sqlmodel import Session
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info
from strawberry.extensions import SchemaExtension

from . import utils, models
from .database import engine
from .models import ShotModel, SignalModel

T = TypeVar("T")


@strawberry.input()
class ComparatorFilter(Generic[T]):
    eq: Optional[T] = None
    neq: Optional[T] = None
    gt: Optional[T] = None
    lt: Optional[T] = None
    gte: Optional[T] = None
    lte: Optional[T] = None
    isNull: Optional[T] = None
    contains: Optional[T] = None


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


class SQLAlchemySession(SchemaExtension):
    def on_request_start(self):
        self.execution_context.context["db"] = Session(
            autocommit=False, autoflush=False, bind=engine, future=True
        )

    def on_request_end(self):
        self.execution_context.context["db"].close()


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
        info: Info,
        where: Optional[SignalWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Annotated["Signal", strawberry.lazy(".graphql")]]:
        return get_signals(info, where, limit)


@strawberry.experimental.pydantic.type(
    model=SignalModel,
    all_fields=True,
    description="Signal objects contain metadata about a signal from a diagnostic.",
)
class Signal:
    @strawberry.field(description="Get information about shots.")
    def shots(
        self,
        info: Info,
        where: Optional[ShotWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Shot]:
        return get_shots(info, where, limit)


@strawberry.experimental.pydantic.type(
    model=models.CPFSummaryModel,
    fields=["name", "description"],
    description="CPF Summary data including a description of each CPF variable",
)
class CPFSummary:
    pass


@strawberry.experimental.pydantic.type(
    model=models.ScenarioModel,
    fields=["name"],
    description="Information about different scenarios.",
)
class Scenario:
    pass


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


def get_shots(info: Info, where: ShotWhereFilter, limit: int) -> List[Shot]:
    """Query database for shots"""
    db = info.context["db"]
    query = db.query(models.ShotModel)
    query = do_where(ShotModel, query, where)
    query = query.order_by(ShotModel.shot_id.desc())
    query = query.limit(limit) if limit is not None else query
    rows = query.all()
    return rows


def get_signals(info: Info, where: SignalWhereFilter, limit: int) -> List[Signal]:
    """Query database for signals"""
    db = info.context["db"]
    query = db.query(models.SignalModel)
    query = do_where(SignalModel, query, where)
    query = query.order_by(SignalModel.name)
    query = query.limit(limit) if limit is not None else query
    rows = query.all()
    return rows


def get_cpf_summary(info: Info):
    """Query database for CPF metadata"""
    db = info.context["db"]
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.name)
    rows = query.all()
    return rows


def get_scenarios(info: Info):
    """Query database for scenario metadata"""
    db = info.context["db"]
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.name)
    rows = query.all()
    return rows


@strawberry.type
class Query:
    @strawberry.field(description="Get information about different shots.")
    def shots(
        self,
        info: Info,
        where: Optional[ShotWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Shot]:
        return get_shots(info, where, limit)

    @strawberry.field(
        description="Get information about signals from diagnostic equipment."
    )
    def signals(
        self,
        info: Info,
        where: Optional[SignalWhereFilter] = None,
        limit: Optional[int] = None,
    ) -> List[Signal]:
        return get_signals(info, where, limit)

    @strawberry.field(description="Get information about CPF variables.")
    def cpf_summary(
        self,
        info: Info,
    ) -> List[CPFSummary]:
        return get_cpf_summary(info)

    @strawberry.field(description="Get information about different scenarios.")
    def scenarios(
        self,
        info: Info,
    ) -> List[Scenario]:
        return get_scenarios(info)


schema = strawberry.Schema(
    query=Query,
    extensions=[SQLAlchemySession],
    config=StrawberryConfig(auto_camel_case=False),
)
