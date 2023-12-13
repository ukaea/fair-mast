import sqlmodel
import uuid
import h5py
from typing import List, get_type_hints, Annotated, Optional

from fastapi import (
    Depends,
    Query,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import (
    HTMLResponse,
    StreamingResponse,
    JSONResponse,
    FileResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from strawberry.asgi import GraphQL
from strawberry.fastapi import GraphQLRouter

import pandas as pd
import json
import ndjson
import io
from . import crud, models, graphql, utils
from .types import FileType
from .page import MetadataPage
from .utils import InputParams
from .database import SessionLocal, engine, get_db
from pydantic import create_model
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate
from strawberry.fastapi import GraphQLRouter
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

templates = Jinja2Templates(directory="src/api/templates")


class JSONLDGraphQL(GraphQL):
    async def process_result(
        self, request: Request, result: ExecutionResult
    ) -> GraphQLHTTPResponse:
        def fixup_context(d):
            if not isinstance(d, dict):
                return d

            for k, v in zip(list(d.keys()), d.values()):
                if isinstance(v, dict):
                    d[k] = fixup_context(v)
                if isinstance(v, list):
                    d[k] = [fixup_context(item) for item in v]
                elif k.endswith("_"):
                    d[f"@{k[:-1]}"] = d.pop(k)
            return d

        data: GraphQLHTTPResponse = {"data": result.data}

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]

        if result.errors:
            data["errors"] = [err.formatted for err in result.errors]
        if result.extensions:
            data["extensions"] = result.extensions

        data = fixup_context(data)
        data: GraphQLHTTPResponse = data
        return data


graphql_app = JSONLDGraphQL(
    graphql.schema,
)


# Setup FastAPI Application
app = FastAPI(title="MAST Archive", servers=[{"url": "http://localhost:8081/json"}])
app.mount("/html", StaticFiles(directory="./src/api/static/html"))
app.mount("/data", StaticFiles(directory="data"))
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

DEFAULT_PER_PAGE = 50


def parse_query_params(
    fields: Optional[str] = None,
    filters: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 0,
    per_page: int = DEFAULT_PER_PAGE,
):
    fields = fields.split(",") if fields is not None else []
    filters = filters.split(",") if filters is not None else []
    return QueryParams(fields, filters, sort, page, per_page)


def parse_aggregate_query_params(
    data: Optional[str] = None,
    groupby: Optional[str] = None,
    filters: Optional[str] = None,
    sort: Optional[str] = None,
    page: int = 0,
    per_page: int = DEFAULT_PER_PAGE,
):
    data = data.split(",") if data is not None else []
    groupby = groupby.split(",") if groupby is not None else []
    filters = filters.split(",") if filters is not None else []
    return AggregateQueryParams(data, groupby, filters, sort, page, per_page)


class QueryParams:
    def __init__(
        self,
        fields: List[str] = Query(
            None,
            description="Comma seperated list of fields to include",
        ),
        filters: List[str] = Query(
            None, description="Comma seperated list of filters to include"
        ),
        sort: Optional[str] = Query(None, description="Column to sort data by."),
        page: int = Query(default=0, description="Page number to get."),
        per_page: int = Query(
            default=50, description="Number of items to get per page."
        ),
    ):
        self.fields = fields
        self.filters = filters
        self.sort = sort
        self.page = page
        self.per_page = per_page


class AggregateQueryParams:
    def __init__(
        self,
        data: str = None,
        groupby: str = None,
        filters: str = None,
        sort: str = None,
        page: int = Query(default=0, description="Page number to get."),
        per_page: int = Query(
            default=50, description="Number of items to get per page."
        ),
    ):
        self.data = data
        self.groupby = groupby
        self.filters = filters
        self.sort = sort
        self.page = page
        self.per_page = per_page


def apply_pagination(
    request: Request,
    response: Response,
    db: Session,
    query: crud.Query,
    params: AggregateQueryParams | QueryParams,
) -> crud.Query:
    query = crud.apply_pagination(query, params.page, params.per_page)
    headers = crud.get_pagination_metadata(
        db, query, params.page, params.per_page, request.url
    )
    response.headers.update(headers)
    return query


def query_all(
    request: Request,
    response: Response,
    db: Session,
    model_cls: type[sqlmodel.SQLModel],
    params: QueryParams,
):
    query = crud.select_query(model_cls, params.fields, params.filters, params.sort)
    query = apply_pagination(request, response, db, query, params)
    items = crud.execute_query_all(db, query)
    return items


def query_aggregate(
    request: Request,
    response: Response,
    db: Session,
    model_cls: type[sqlmodel.SQLModel],
    params: AggregateQueryParams,
):
    query = crud.aggregate_query(
        model_cls, params.data, params.groupby, params.filters, params.sort
    )

    query = apply_pagination(request, response, db, query, params)
    items = db.execute(query).all()
    return items


@app.api_route(
    "/json/shots",
    methods=["GET", "HEAD"],
    description="Get information about experimental shots",
    response_model_exclude_unset=True,
)
def get_shots(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(parse_query_params),
) -> List[models.ShotModel]:
    shots = query_all(request, response, db, models.ShotModel, params)
    return shots


@app.get("/json/shots/aggregate")
def get_shots_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(parse_aggregate_query_params),
):
    items = query_aggregate(request, response, db, models.ShotModel, params)
    return items


@app.get(
    "/json/shots/{shot_id}",
    description="Get information about a single experimental shot",
)
def get_shot(db: Session = Depends(get_db), shot_id: int = None) -> models.ShotModel:
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model_exclude_unset=True,
)
def get_signals_for_shot(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    shot_id: int = None,
    params: QueryParams = Depends(parse_query_params),
) -> List[models.SignalModel]:
    # Get shot
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)

    # Get signals for this shot
    params.filters.append(f"shot_id$eq{shot['shot_id']}")
    signals = crud.get_signals(params.sort, params.fields, params.filters)

    signals = apply_pagination(request, response, db, signals, params)
    signals = crud.execute_query_all(db, signals)
    return signals


@app.get(
    "/json/shots/{shot_id}/signal_datasets",
    description="Get information all signal datasts for a single shot",
    response_model_exclude_unset=True,
)
def get_signal_datasets_shots(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    shot_id: int = None,
    params: QueryParams = Depends(parse_query_params),
) -> List[models.SignalDatasetModel]:
    # First find the signals for this shot
    signals = crud.get_signals(filters=[f"shot_id$eq{shot_id}"])
    signals = crud.execute_query_all(db, signals)
    signal_names = [item["signal_name"] for item in signals]

    # Then find the datasets for those signals
    datasets = db.query(models.SignalDatasetModel)
    datasets = datasets.filter(models.SignalDatasetModel.name.in_(signal_names))
    datasets = crud.apply_parameters(
        datasets, models.SignalDatasetModel, params.fields, params.filters, params.sort
    )

    datasets = apply_pagination(request, response, db, datasets, params)
    datasets = crud.execute_query_all(db, datasets)
    return datasets


@app.get(
    "/json/signal_datasets/",
    description="Get information about different signal datasets.",
    response_model_exclude_unset=True,
)
def get_signal_datasets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(parse_query_params),
) -> List[models.SignalDatasetModel]:
    datasets = query_all(request, response, db, models.SignalDatasetModel, params)
    return datasets


@app.get("/json/signal_datasets/aggregate")
def get_signal_datasets_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(parse_aggregate_query_params),
):
    items = query_aggregate(request, response, db, models.SignalDatasetModel, params)
    return items


@app.get(
    "/json/signal_datasets/{name}",
    description="Get information about a single signal dataset",
    response_model_exclude_unset=True,
)
def get_signal_dataset(
    db: Session = Depends(get_db), name: str = None
) -> models.SignalDatasetModel:
    signal_dataset = crud.get_signal_dataset(name)
    signal_dataset = crud.execute_query_one(db, signal_dataset)
    return signal_dataset


@app.get(
    "/json/signal_datasets/{name}/shots",
    description="Get information all shots for a single signal dataset",
    response_model_exclude_unset=True,
)
def get_shots_for_signal_datasets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    name: str = None,
    params: QueryParams = Depends(parse_query_params),
) -> List[models.ShotModel]:
    # Get signals with given signal name
    signals = crud.get_signals(filters=[f"signal_name$eq{name}"])
    signals = crud.execute_query_all(db, signals)
    shot_ids = [item["shot_id"] for item in signals]

    # Get all shots for those signals
    query = db.query(models.ShotModel)
    query = query.filter(models.ShotModel.shot_id.in_(shot_ids))
    query = crud.apply_parameters(
        query, models.ShotModel, params.fields, params.filters, params.sort
    )

    shots = apply_pagination(request, response, db, datasets, params)
    shots = crud.execute_query_all(db, query)
    return shots


@app.get(
    "/json/signal_datasets/{name}/signals",
    description="Get information all signals for a single signal dataset",
    response_model_exclude_unset=True,
)
def get_signals_for_signal_datasets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    name: str = None,
    params: QueryParams = Depends(parse_query_params),
) -> List[models.SignalModel]:
    params.filters.append(f"signal_name$eq{name}")
    query = crud.get_signals(params.sort, params.fields, params.filters)

    signals = apply_pagination(request, response, db, signals, params)
    signals = crud.execute_query_all(db, query)
    return signals


@app.get(
    "/json/signals/",
    description="Get information about specific signals.",
    response_model_exclude_unset=True,
)
def get_signals(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(parse_query_params),
) -> List[models.SignalModel]:
    signals = query_all(request, response, db, models.SignalModel, params)
    return signals


@app.get("/json/signals/aggregate")
def get_signals_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(parse_aggregate_query_params),
):
    items = query_aggregate(request, response, db, models.SignalModel, params)
    return items


@app.get(
    "/json/signals/{uuid_}",
    description="Get information about a single signal",
    response_model_exclude_unset=True,
)
def get_signal(
    db: Session = Depends(get_db), uuid_: uuid.UUID = None
) -> models.SignalModel:
    signal = crud.get_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    return signal


@app.get(
    "/json/signals/{uuid_}/shot",
    description="Get information about the shot for a single signal",
    response_model_exclude_unset=True,
)
def get_shot_for_signal(
    db: Session = Depends(get_db), uuid_: uuid.UUID = None
) -> models.ShotModel:
    signal = crud.get_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    shot = crud.get_shot(signal["shot_id"])
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/signals/{uuid_}/signal_dataset",
    description="Get information about the dataset for a single signal",
    response_model_exclude_unset=True,
)
def get_shot_for_signal(
    db: Session = Depends(get_db), uuid_: uuid.UUID = None
) -> models.SignalDatasetModel:
    signal = crud.get_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    dataset = crud.get_signal_dataset(signal["signal_name"])
    dataset = crud.execute_query_one(db, dataset)
    return dataset


@app.get(
    "/json/cpf_summary/",
    description="Get descriptions of CPF summary variables.",
)
def get_cpf_summary(
    db: Session = Depends(get_db),
) -> List[models.CPFSummaryModel]:
    summary = crud.get_cpf_summary(db)
    return summary.all()


@app.get(
    "/json/scenarios/",
    description="Get information on different scenarios.",
)
def get_scenarios(
    db: Session = Depends(get_db),
) -> List[models.ScenarioModel]:
    scenarios = crud.get_scenarios(db)
    return scenarios.all()


@app.get(
    "/json/sources",
    description="Get information on different sources.",
)
def get_sources(
    db: Session = Depends(get_db),
) -> List[models.SourceModel]:
    sources = crud.get_sources(db)
    return sources.all()


@app.get(
    "/json/sources/{name}",
    description="Get information about a single signal",
)
def get_signal(db: Session = Depends(get_db), name: str = None) -> models.SourceModel:
    source = crud.get_source(db, name)
    source = db.execute(source).one()[0]
    return source


@app.get(
    "/json/image_metadata",
    description="Get image metadata from signals.",
)
def get_image_metadata(
    db: Session = Depends(get_db),
) -> List[models.ImageMetadataModel]:
    sources = crud.get_image_metadata(db)
    return sources.all()


@app.get(
    "/meta_catalog.yml",
    description="Get the meta data catalog.",
)
def get_meta_catalog(db: Session = Depends(get_db)) -> FileResponse:
    return FileResponse("data/meta.yml")


@app.get(
    "/files/shots",
    description="Get a file of shot information.",
)
def get_shots_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.ShotModel)
    query = query.order_by(models.ShotModel.shot_id.desc())
    return crud.get_table_as_dataframe(query, "shots", format)


@app.get(
    "/files/signal_datasets",
    description="Get a file of signal dataset information.",
)
def get_signal_datasets_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SignalDatasetModel)
    query = query.order_by(models.SignalDatasetModel.signal_dataset_id)
    return crud.get_table_as_dataframe(query, "signal_datasets", format)


@app.get(
    "/files/signals",
    description="Get a file of signal information.",
)
def get_signals_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SignalModel)
    query = query.order_by(models.SignalModel.id)
    return crud.get_table_as_dataframe(query, "signals", format)


@app.get(
    "/files/scenarios",
    description="Get a file of scenarios information.",
)
def get_scenarios_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.id)
    return crud.get_table_as_dataframe(query, "scenarios", format)


@app.get(
    "/files/sources",
    description="Get a file of sources information.",
)
def get_sources_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SourceModel)
    query = query.order_by(models.SourceModel.name)
    return crud.get_table_as_dataframe(query, "sources", format)


@app.get(
    "/files/cpf_summary",
    description="Get a file of CPF summary information.",
)
def get_cpf_summary_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.index)
    return crud.get_table_as_dataframe(query, "cpf_summary", format)
