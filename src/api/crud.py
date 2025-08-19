import io
import math
import re
import typing as t
import uuid

import pandas as pd
import sqlmodel
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, load_only
from sqlalchemy.sql import column, select
from sqlalchemy.sql.expression import Select

from . import models
from .database import engine
from .utils import aggregate_map, comparator_map

COMPARATOR_NAMES_DESCRIPTION = ", ".join(
    ["$" + name + ":" for name in comparator_map.keys()]
)
AGGREGATE_NAMES_DESCRIPTION = ", ".join(
    ["$" + name + ":" for name in aggregate_map.keys()]
)

Query = Select[t.Any]

MEDIA_TYPES = {
    "parquet": "binary",
    "csv": "text",
}

DF_EXPORT_FUNCS = {
    "parquet": lambda df, stream: df.to_parquet(stream),
    "csv": lambda df, stream: df.to_csv(stream),
}


def apply_filters(query: Query, filters: str) -> Query:
    comparator_names = list(comparator_map.keys())
    comparator_names = ["\$" + name + ":" for name in comparator_names]
    comparator_names = "|".join(comparator_names)

    filters = [
        re.split(
            f"({comparator_names})",
            item,
        )
        for item in filters
    ]

    padded_filters = []
    for item in filters:
        if item[-1] == "":
            item[-1] = None
        padded_filters.append(item)

    for name, op, value in padded_filters:
        op = op.replace("$", "")
        op = op.replace(":", "")
        func = comparator_map[op]
        query = query.filter(func(column(name), value))

    return query


def apply_sorting(query: Query, sort: t.Optional[str] = None) -> Query:
    if sort is None:
        return query

    if sort.startswith("-"):
        sort = sort[1:]
        order = desc(column(sort))
    else:
        order = column(sort)

    query = query.order_by(order)
    return query


def apply_pagination(query: Query, page: int, per_page: int) -> Query:
    query = query.limit(per_page).offset(page * per_page)
    return query


def apply_fields(
    query: Query, model_cls: type[sqlmodel.SQLModel], fields: str
) -> Query:
    if len(fields) == 0:
        return query

    fields.extend(["context", "type", "title"])
    query = query.options(load_only(*fields))
    return query


def create_aggregate_columns(aggregates):
    agg_funcs = [item.split("$") for item in aggregates]
    parts = []
    for name, func_name in agg_funcs:
        func_name = func_name.replace(":", "")
        part = aggregate_map[func_name](column(name))
        if func_name != "distinct":
            part = part.label(f"{func_name}_{name}")
        else:
            part = part.label(f"{name}")
        parts.append(part)

    return parts


def select_query(
    model_cls: type[sqlmodel.SQLModel],
    fields: t.List[str] = [],
    filters: t.List[str] = [],
    sort: t.Optional[str] = None,
) -> Query:
    query = select(model_cls)
    query = apply_parameters(query, model_cls, fields, filters, sort)
    return query


def apply_parameters(
    query,
    model_cls: type[sqlmodel.SQLModel],
    fields: t.List[str],
    filters: t.List[str],
    sort: str,
):
    query = apply_fields(query, model_cls, fields)
    query = apply_filters(query, filters)
    query = apply_sorting(query, sort)
    return query


def aggregate_query(
    model_cls: type[sqlmodel.SQLModel],
    data: t.List[str],
    groupby: t.List[str],
    filters: t.List[str],
    sort: t.Optional[str] = None,
) -> Query:
    aggregate_columns = create_aggregate_columns(data)
    groupby = [column(item) for item in groupby]

    for item in groupby:
        aggregate_columns.append(item)

    query = select(from_obj=model_cls, columns=aggregate_columns)
    query = apply_filters(query, filters)

    if sort is not None:
        query = apply_sorting(query, sort)

    query = query.group_by(*groupby)
    return query


def get_required_field_names(cls_):
    names = []
    for key, value in cls_.__fields__.items():
        if value.required:
            names.append(key)
    return names


def execute_query_all(db: Session, query: Query):
    items = db.execute(query)
    items = [item[0].dict(exclude_none=True) for item in items]
    return items


def execute_query_one(db: Session, query: Query):
    item = db.execute(query).one()[0]
    item = item.dict(exclude_none=True, by_alias=True)
    return item


def get_pagination_metadata(
    db: Session, query: Query, page: int, per_page: int, url: str
) -> t.Dict[str, str]:
    count_query = select(func.count()).select_from(query)
    total_count = db.execute(count_query).scalar_one()
    total_pages = math.ceil(total_count / per_page)

    link = ""
    if page + 1 < total_pages:
        item = str(url).replace(f"page={page}", f"page={page+1}")
        link += f'<{item}>; rel="next"'

    if page > 0:
        item = str(url).replace(f"page={page}", f"page={page-1}")
        link += f'<{item}>; rel="previous"'

    headers = {
        "X-Total-Count": str(total_count),
        "X-Total-Pages": str(total_pages),
        "link": link,
    }
    return headers


def get_shots(
    sort: t.Optional[str] = "-shot_id",
    fields: t.Optional[t.List[str]] = None,
    filters: t.Optional[t.List[str]] = None,
):
    query = select_query(models.ShotModel, fields, filters, sort)
    return query


def get_shot_aggregate(*args):
    query = aggregate_query(models.ShotModel, *args)
    return query


def get_shot(shot_id: int):
    query = select(models.ShotModel)
    query = query.filter(models.ShotModel.shot_id == shot_id)
    return query


def get_level2_shot(shot_id: int):
    query = select(models.Level2ShotModel)
    query = query.filter(models.Level2ShotModel.shot_id == shot_id)
    return query


def get_dataservices(db: Session):
    query = select(models.DataService)
    query = db.execute(query).one()[0]
    return query


def get_signal_datasets(
    sort: t.Optional[str] = "name",
    fields: t.Optional[t.List[str]] = [],
    filters: t.Optional[t.List[str]] = [],
):
    query = select_query(models.SignalDatasetModel, fields, filters, sort)
    return query


def get_signal_datasets_aggregate(*args):
    query = aggregate_query(models.SignalDatasetModel, *args)
    return query


def get_signal_dataset(uuid: uuid.UUID):
    query = select(models.SignalDatasetModel)
    query = query.filter(models.SignalDatasetModel.uuid == uuid)
    return query


def get_signals(
    sort: t.Optional[str] = "-shot_id",
    fields: t.Optional[t.List[str]] = [],
    filters: t.Optional[t.List[str]] = [],
):
    query = select_query(models.SignalModel, fields, filters, sort)
    return query


def get_signal(uuid_: uuid.UUID):
    query = select(models.SignalModel)
    query = query.filter(models.SignalModel.uuid == uuid_)
    return query


def get_level2_signal(uuid_: uuid.UUID):
    query = select(models.Level2SignalModel)
    query = query.filter(models.Level2SignalModel.uuid == uuid_)
    return query


def get_cpf_summary(db: Session):
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.name)
    return query


def get_scenarios(db: Session):
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.name)
    return query


def get_sources(db: Session):
    query = db.query(models.SourceModel)
    query = query.order_by(models.SourceModel.name)
    return query


def get_source(db: Session, uuid_: uuid.UUID):
    query = db.query(models.SourceModel)
    query = query.filter(models.SourceModel.uuid == uuid_)
    return query


def get_level2_source(db: Session, uuid_: uuid.UUID):
    query = db.query(models.Level2SourceModel)
    query = query.filter(models.Level2SourceModel.uuid == uuid_)
    return query


def get_image_metdata(db: Session):
    query = db.query(models.ImageMetadataModel)
    query = query.order_by(models.ImageMetadataModel.name)
    return query


def get_table_as_dataframe(query, name: str, ext: str = "parquet"):
    if ext not in MEDIA_TYPES:
        raise RuntimeError(f"Unknown extension type {ext}")

    media_type = MEDIA_TYPES[ext]

    df = pd.read_sql(query.statement, con=engine.connect())
    columns = df.columns
    for column_item in columns:
        if df[column_item].dtype == uuid.UUID:
            df[column_item] = df[column_item].astype(str)

    stream = io.BytesIO() if media_type == "binary" else io.StringIO()
    DF_EXPORT_FUNCS[ext](df, stream)

    response = StreamingResponse(
        iter([stream.getvalue()]), media_type=f"{media_type}/{ext}"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={name}.{ext}"
    return response
