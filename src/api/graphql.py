from base64 import b64encode, b64decode
from typing import List, Generic, TypeVar, Optional, get_type_hints, Annotated
from dataclasses import asdict, make_dataclass, field
from sqlalchemy import func
from sqlmodel import Session, select
from sqlalchemy.engine.row import Row
import strawberry
from strawberry.schema.config import StrawberryConfig
from strawberry.types import Info
from strawberry.extensions import SchemaExtension
from sqlalchemy.orm import selectinload

from . import utils, models
from .database import engine
from .models import ShotModel, SignalDatasetModel, SignalModel

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
SignalDatasetWhereFilter = make_where_filter(models.SignalDatasetModel)
SourceWhereFilter = make_where_filter(models.SourceModel)
SignalWhereFilter = make_where_filter(models.SignalModel)

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


def paginate(
    info: Info,
    response_type,
    model,
    item_name: str,
    cursor_name: str,
    query,
    cursor: str,
    limit: int,
    default_cursor_value=-1,
) -> "PagedResponse":
    db = info.context["db"]
    # pagiantion: get next cursor for pagiantion
    cursor = decode_cursor(cursor) if cursor is not None else default_cursor_value

    # get total items
    total_items_query = select(func.count()).select_from(query.subquery())
    total_items = db.exec(total_items_query).one()

    query = query.where(getattr(model, cursor_name) > cursor)
    items = db.exec(query.limit(limit)).all()

    # Special case: if we get a row response, take the first element
    if len(items) > 0 and isinstance(items[0], Row):
        items = [item[0] for item in items]

    last_cursor = (
        encode_cursor(getattr(items[-1], cursor_name)) if len(items) > 0 else None
    )

    return response_type(
        **{item_name: items},
        page_meta=PageMeta(last_cursor=last_cursor, total_items=total_items),
    )


def get_shots(
    info: Info,
    where: Optional[ShotWhereFilter] = None,
    limit: Optional[int] = 10,
    cursor: Optional[str] = None,
) -> Annotated["ShotResponse", strawberry.lazy(".graphql")]:
    """Query database for shots"""
    query = select(models.ShotModel)
    query = query.order_by(models.ShotModel.shot_id)

    # Build the query
    query = do_where(models.ShotModel, query, where)
    query = query.options(selectinload(models.ShotModel.signal_datasets))

    return paginate(
        info, ShotResponse, models.ShotModel, "shots", "shot_id", query, cursor, limit
    )


def get_signal_datasets(
    info: Info,
    where: Optional[SignalDatasetWhereFilter] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> Annotated["SignalDatasetResponse", strawberry.lazy(".graphql")]:
    """Query database for signals"""
    query = select(models.SignalDatasetModel)
    query = query.order_by(models.SignalDatasetModel.signal_dataset_id)
    query = do_where(models.SignalDatasetModel, query, where)
    query = query.options(selectinload(models.SignalDatasetModel.shots))
    return paginate(
        info,
        SignalDatasetResponse,
        models.SignalDatasetModel,
        "signal_datasets",
        "signal_dataset_id",
        query,
        cursor,
        limit,
    )


def get_sources(
    info: Info,
    where: Optional[SourceWhereFilter] = None,
    limit: Optional[int] = None,
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
        "name",
        query,
        cursor,
        limit,
        default_cursor_value="",
    )


def get_signals(
    info: Info,
    where: Optional[SignalWhereFilter] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> Annotated["SignalResponse", strawberry.lazy(".graphql")]:
    """Query database for source metadata"""
    db = info.context["db"]
    query = db.query(models.SignalModel)
    query = do_where(models.SignalModel, query, where)
    query = query.order_by(models.SignalModel.id)
    return paginate(
        info,
        SignalResponse,
        models.SignalModel,
        "signals",
        "id",
        query,
        cursor,
        limit,
        default_cursor_value=-1,
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
    get_signal_datasets: Annotated[
        "SignalDatasetResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_signal_datasets,
        description="Get information about signals from diagnostic equipment.",
    )

    get_sources: Annotated[
        "SourceResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_sources,
        description="Get information about sources of datasets for a shot.",
    )

    get_signals: Annotated[
        "SignalResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_signals, description="Get information about specific signals."
    )


@strawberry.experimental.pydantic.type(
    model=SignalDatasetModel,
    all_fields=True,
    description="SignalDataset objects contain metadata about a signal dataset.",
)
class SignalDataset:
    context_: str = strawberry.field(name="context_")
    type_: str = strawberry.field(name="type_")

    get_shots: Annotated[
        "ShotResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_shots, description="Get information about different shots."
    )

    get_signals: Annotated[
        "SignalResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_signals, description="Get information about specific signals."
    )

    get_sources: Annotated[
        "SourceResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_sources,
        description="Get information about sources of datasets for a shot.",
    )


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
    get_shots: Annotated[
        "ShotResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_shots, description="Get information about different shots."
    )

    get_signals: Annotated[
        "SignalResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_signals, description="Get information about specific signals."
    )

    get_signal_datasets: Annotated[
        "SignalDatasetResponse", strawberry.lazy(".graphql")
    ] = strawberry.field(
        resolver=get_signal_datasets,
        description="Get information about signals from diagnostic equipment.",
    )


@strawberry.type
class PageMeta:
    total_items: int = strawberry.field(
        description="The total number of items in the database."
    )
    last_cursor: Optional[str] = strawberry.field(
        description="The cursor of the last item to continue the pagination."
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
class SignalDatasetResponse(PagedResponse):
    signal_datasets: List[SignalDataset] = strawberry.field(
        description="A list of signals datasets."
    )


@strawberry.type
class SourceResponse(PagedResponse):
    sources: List[Source] = strawberry.field(description="A list of sources.")


@strawberry.type
class SignalResponse(PagedResponse):
    signals: List[Signal] = strawberry.field(description="A list of signals.")


@strawberry.type
class Query:
    get_shots: ShotResponse = strawberry.field(
        resolver=get_shots, description="Get information about different shots."
    )

    get_signal_datasets: SignalDatasetResponse = strawberry.field(
        resolver=get_signal_datasets,
        description="Get information about signals from diagnostic equipment.",
    )

    get_sources: SourceResponse = strawberry.field(
        resolver=get_sources, description="Get information about different sources."
    )

    get_signals: SignalResponse = strawberry.field(
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
)
