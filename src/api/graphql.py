import math
from base64 import b64decode, b64encode
from dataclasses import asdict, field, make_dataclass
from typing import Annotated, Generic, List, Optional, TypeVar, get_type_hints

import strawberry
from sqlalchemy import func
from sqlalchemy.engine.row import Row
from sqlmodel import Session, select
from strawberry.extensions import SchemaExtension
from strawberry.scalars import JSON
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info

from . import models, utils
from .database import engine
from .models import ShotModel, SignalModel, SourceModel

T = TypeVar("T")

GRAPHQL_PAGINATION_LIMIT = 50


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
            if not utils.is_list(field_type) and field_type not in [
                ShotModel,
                SignalModel,
                SourceModel,
            ]:
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
SourceWhereFilter = make_where_filter(models.SourceModel)
SignalWhereFilter = make_where_filter(models.SignalModel)


def do_where_child_member(results, where):
    if where is None:
        return results

    where = asdict(where)
    for name, filters in where.items():
        if filters is not None:
            for op_name, value in filters.items():
                if value is not None:
                    op = utils.comparator_map[op_name]
                    results = list(
                        filter(lambda item: op(getattr(item, name), value), results)
                    )
    return results


def do_where(model_cls, query, where):
    if where is None:
        return query

    where = asdict(where)
    for name, filters in where.items():
        if filters is not None:
            for op_name, value in filters.items():
                if value is not None:
                    op = utils.comparator_map[op_name]
                    query = query.filter(op(getattr(model_cls, name), value))
    return query


def paginate(
    info: Info,
    response_type,
    model,
    item_name: str,
    query,
    cursor: str,
    limit: int,
) -> "PagedResponse":
    db = info.context["db"]
    # pagiantion: get next cursor for pagiantion

    # get total items and pages
    total_items_query = select(func.count()).select_from(query.subquery())
    total_items = db.exec(total_items_query).one()
    total_pages = math.ceil(total_items / limit)

    if cursor is not None:
        offset = decode_cursor(cursor)
    else:
        offset = 0

    query = query.offset(offset)
    items = db.exec(query.limit(limit)).all()

    # Special case: if we get a row response, take the first element
    if len(items) > 0 and isinstance(items[0], Row):
        items = [item[0] for item in items]

    next_cursor = None
    # if we have results encode the next cursor
    if len(items) > 0:
        next_cursor = encode_cursor(offset + limit)

    # if we have less items than the limit we must be at the end,
    # set next cursor to None
    if len(items) < limit:
        next_cursor = None

    return response_type(
        **{item_name: items},
        page_meta=PageMeta(
            next_cursor=next_cursor, total_items=total_items, total_pages=total_pages
        ),
    )


def get_shots(
    info: Info,
    where: Optional[ShotWhereFilter] = None,
    limit: Optional[int] = GRAPHQL_PAGINATION_LIMIT,
    cursor: Optional[str] = None,
) -> Annotated["ShotResponse", strawberry.lazy(".graphql")]:
    """Query database for shots"""
    query = select(models.ShotModel)
    query = query.order_by(models.ShotModel.shot_id)

    # Build the query
    query = do_where(models.ShotModel, query, where)

    return paginate(info, ShotResponse, models.ShotModel, "shots", query, cursor, limit)


def get_sources(
    info: Info,
    where: Optional[SourceWhereFilter] = None,
    limit: Optional[int] = GRAPHQL_PAGINATION_LIMIT,
    cursor: Optional[str] = None,
) -> Annotated["SourceResponse", strawberry.lazy(".graphql")]:
    """Query database for source metadata"""
    db = info.context["db"]
    query = db.query(models.SourceModel)
    query = do_where(models.SourceModel, query, where)
    query = query.order_by(models.SourceModel.name)
    return paginate(
        info,
        SourceResponse,
        models.SourceModel,
        "sources",
        query,
        cursor,
        limit,
    )


def get_signals(
    info: Info,
    where: Optional[SignalWhereFilter] = None,
    limit: Optional[int] = GRAPHQL_PAGINATION_LIMIT,
    cursor: Optional[str] = None,
) -> Annotated["SignalResponse", strawberry.lazy(".graphql")]:
    """Query database for source metadata"""
    db = info.context["db"]
    query = db.query(models.SignalModel)
    query = do_where(models.SignalModel, query, where)
    query = query.order_by(models.SignalModel.shot_id)
    return paginate(
        info,
        SignalResponse,
        models.SignalModel,
        "signals",
        query,
        cursor,
        limit,
    )


def get_cpf_summary(info: Info) -> List["CPFSummary"]:
    """Query database for CPF metadata"""
    db = info.context["db"]
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.name)
    rows = query.all()
    return rows


def get_scenarios(info: Info) -> List["Scenario"]:
    """Query database for scenario metadata"""
    db = info.context["db"]
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.name)
    rows = query.all()
    return rows


def encode_cursor(id: int) -> str:
    """
    Encodes the given ID into a cursor.

    :param id: The ID to encode.

    :return: The encoded cursor.
    """
    return b64encode(f"{id}".encode("ascii")).decode("ascii")


def decode_cursor(cursor: str) -> int:
    """
    Decodes the ID from the given cursor.

    :param cursor: The cursor to decode.

    :return: The decoded user ID.
    """
    cursor_data = b64decode(cursor.encode("ascii")).decode("ascii")
    return int(cursor_data)


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
    @strawberry.field
    def signals(
        self,
        info: Info,
        limit: Optional[int] = None,
        where: Optional[SignalWhereFilter] = None,
    ) -> List[strawberry.LazyType["Signal", __module__]]:  # noqa: F821
        results = get_signals(info, where, limit)
        results = results.signals
        return results

    @strawberry.field
    def sources(
        self,
        info: Info,
        limit: Optional[int] = None,
        where: Optional[SourceWhereFilter] = None,
    ) -> List[strawberry.LazyType["Source", __module__]]:  # noqa: F821
        results = get_sources(info, where, limit)
        results = results.souces
        return results


@strawberry.experimental.pydantic.type(
    model=models.CPFSummaryModel,
    description="CPF Summary data including a description of each CPF variable",
)
class CPFSummary:
    name: strawberry.auto
    description: strawberry.auto


@strawberry.experimental.pydantic.type(
    model=models.ScenarioModel,
    description="Information about different scenarios.",
)
class Scenario:
    name: strawberry.auto


@strawberry.experimental.pydantic.type(
    model=models.SourceModel,
    all_fields=True,
    description="Information about different sources.",
)
class Source:
    pass


@strawberry.experimental.pydantic.type(
    model=models.SignalModel,
    all_fields=True,
    description="Information about different sources.",
)
class Signal:
    shot: Shot


@strawberry.type
class PageMeta:
    total_items: int = strawberry.field(
        description="The total number of items in the database."
    )

    total_pages: int = strawberry.field(
        description="The total number of pages for all the items."
    )

    next_cursor: Optional[str] = strawberry.field(
        description="The cursor to the next item to continue the pagination."
    )


@strawberry.interface
class PagedResponse:
    page_meta: PageMeta = strawberry.field(
        description="Metadata to aid with pagination."
    )


@strawberry.type
class ShotResponse(PagedResponse):
    shots: List[Shot] = strawberry.field(description="A list of experimental shots.")


@strawberry.type
class SourceResponse(PagedResponse):
    sources: List[Source] = strawberry.field(description="A list of sources.")


@strawberry.type
class SignalResponse(PagedResponse):
    signals: List[Signal] = strawberry.field(description="A list of signals.")


@strawberry.type
class Query:
    all_shots: ShotResponse = strawberry.field(
        resolver=get_shots, description="Get information about different shots."
    )

    all_sources: SourceResponse = strawberry.field(
        resolver=get_sources, description="Get information about different sources."
    )

    all_signals: SignalResponse = strawberry.field(
        resolver=get_signals, description="Get information about specific signals."
    )

    cpf_summary: List[CPFSummary] = strawberry.field(
        resolver=get_cpf_summary, description="Get information about CPF variables."
    )

    scenarios: List[Scenario] = strawberry.field(
        resolver=get_scenarios, description="Get information about different scenarios."
    )


schema = strawberry.Schema(
    query=Query,
    extensions=[SQLAlchemySession],
    config=StrawberryConfig(auto_camel_case=False),
    scalar_overrides={
        dict: JSON,
    },
)
