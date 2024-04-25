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
import os
from . import crud, models, graphql, utils
from .types import FileType
from .page import MetadataPage
from .utils import InputParams
from .database import SessionLocal, engine, get_db
from pydantic import BaseModel, Field, create_model
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


SITE_URL = "http://localhost:8081"
if "VIRTUAL_HOST" in os.environ:
    SITE_URL = f"https://{os.environ.get('VIRTUAL_HOST')}"

DEFAULT_PER_PAGE = 50

# Setup FastAPI Application
app = FastAPI(title="MAST Archive", servers=[{"url": SITE_URL}])
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)

def parse_list_field(item: str) -> List[str]:
    items = item.split(",") if item is not None else []
    return items


class QueryParams:
    """Query parameters for a list of objects in the database."""

    def __init__(
        self,
        fields: str = Query(
            default=None,
            description="Comma seperated list of fields to include.",
            examples=[
                "column_a",
                "column_a,column_b",
            ],
        ),
        filters: str = Query(
            None,
            description=f"Comma seperated list of filters to include. The filters parameter takes a comma seperated list of entries of the form \<column name\>\$\<operator\>\<value\>. Valid filter names are `{crud.COMPARATOR_NAMES_DESCRIPTION}`",
            examples=[
                "column_a$eq:10",
                "column_a$leq:10,column_b$eq:hello",
                "column_c$isNull",
            ],
        ),
        sort: Optional[str] = Query(
            None,
            description="Column to sort data by, optionally prefixed with a negative sign to indicate descending order.",
            examples=["column_a", "-column_b"],
        ),
        page: int = Query(default=0, description="Page number to get."),
        per_page: int = Query(
            default=DEFAULT_PER_PAGE, description="Number of items to get per page."
        ),
    ):
        self.fields = parse_list_field(fields)
        self.filters = parse_list_field(filters)
        self.sort = sort
        self.page = page
        self.per_page = per_page


class AggregateQueryParams:
    """Query parameters for a aggregate summary of lists of objects in the database"""

    def __init__(
        self,
        data: str = Query(
            None,
            description=f"Data columns to perform an aggregate over. The data parameter takes a comma seperated list of entries of the form \<column name\>\$\<operator\>:. Valid aggregator names are: `{crud.AGGREGATE_NAMES_DESCRIPTION}`",
            examples=["column_a$max", "column_a$count,column_b$max"],
        ),
        groupby: str = Query(
            None,
            description="Comma seperated list of columns to groupby. Groupby columns will be included in the aggregated response.",
            examples=["column_a", "column_a,column_b"],
        ),
        filters: str = Query(
            None,
            description=f"Comma seperated list of filters to include. The filters parameter takes a comma seperated list of entries of the form \<column name\>\$\<operator\>:\<value\>. Valid filter names are: `{crud.COMPARATOR_NAMES_DESCRIPTION}`",
            examples=[
                "column_a$eq:10",
                "column_a$leq:10,column_b$eq:hello",
                "column_c$isNull",
            ],
        ),
        sort: Optional[str] = Query(
            None,
            description="Column to sort data by, optionally prefixed with a negative sign to indicate descending order.",
            examples=["column_a", "-column_b"],
        ),
        page: int = Query(default=0, description="Page number to get."),
        per_page: int = Query(
            default=50, description="Number of items to get per page."
        ),
    ):
        self.data = parse_list_field(data)
        self.groupby = parse_list_field(groupby)
        self.filters = parse_list_field(filters)
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
    headers = crud.get_pagination_metadata(
        db, query, params.page, params.per_page, request.url
    )
    query = crud.apply_pagination(query, params.page, params.per_page)
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

from .database import get_db
from .models import SignalModel, ShotModel, SignalDatasetModel, SourceModel, ScenarioModel, CPFSummaryModel
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination.cursor import CursorPage

add_pagination(app)

@app.get(
    "/json/signals",
    description="Get information about specific signals.",
)
def get_signals(
    db: Session = Depends(get_db),
    params: QueryParams = Depends()
    ) -> CursorPage[SignalModel]:
    if params.sort is None:
        params.sort = "uuid"

    query = crud.select_query(SignalModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/shots",
    description="Get information about experimental shots",
)
def get_shots(
    db: Session = Depends(get_db),
    params: QueryParams = Depends()
    ) -> CursorPage[ShotModel]:
    if params.sort is None:
        params.sort = "shot_id"

    query = crud.select_query(ShotModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/signal_datasets",
    description="Get information about different signal datasets.",
)
def get_signal_datasets(
    db: Session = Depends(get_db),
    params: QueryParams = Depends()
    ) -> CursorPage[SignalDatasetModel]:
    if params.sort is None:
        params.sort = "uuid"

    query = crud.select_query(SignalDatasetModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/sources",
    description="Get information on different sources.",
)
def get_sources(
    db: Session = Depends(get_db),
    params: QueryParams = Depends()
    ) -> CursorPage[SourceModel]:
    if params.sort is None:
        params.sort = "name"
    
    query = crud.select_query(SourceModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/scenarios",
    description="Get information on different scenarios.",
)
def get_scenarios(db: Session = Depends(get_db)) -> CursorPage[ScenarioModel]:
    return paginate(db, select(ScenarioModel).order_by(ScenarioModel.id))


@app.get(
    "/json/cpf_summary",
    description="Get descriptions of CPF summary variables.",
)
def get_cpf_summary(db: Session = Depends(get_db)) -> CursorPage[CPFSummaryModel]:
    return paginate(db, select(CPFSummaryModel).order_by(CPFSummaryModel.index))

@app.get(
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
)
def get_signals_for_shot(
    db: Session = Depends(get_db),
    shot_id: int = None,
) -> CursorPage[models.SignalModel]:
    return paginate(db, select(SignalModel).where(SignalModel.shot_id == shot_id).order_by(SignalModel.shot_id))


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
    params: QueryParams = Depends(),
) -> List[models.SignalDatasetModel]:
    # First find the signals for this shot
    signals = crud.get_signals(filters=[f"shot_id$eq:{shot_id}"])
    signals = crud.execute_query_all(db, signals)
    print(signals)
    signal_names = [item["name"] for item in signals]

    # Then find the datasets for those signals
    datasets = db.query(models.SignalDatasetModel)
    datasets = datasets.filter(models.SignalDatasetModel.name.in_(signal_names))
    datasets = crud.apply_parameters(
        datasets, models.SignalDatasetModel, params.fields, params.filters, params.sort
    )

    datasets = apply_pagination(request, response, db, datasets, params)
    datasets = crud.execute_query_all(db, datasets)
    return datasets

@app.get("/json/shots/aggregate")
def get_shots_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
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
    "/json/signal_datasets/aggregate",
    description="Get aggregate information over all datasets.",
)
def get_signal_datasets_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
):
    items = query_aggregate(request, response, db, models.SignalDatasetModel, params)
    return items


@app.get(
    "/json/signal_datasets/{uuid_}",
    description="Get information about a single dataset",
    response_model_exclude_unset=True,
)
def get_signal_dataset(
    db: Session = Depends(get_db),
    uuid_: uuid.UUID = None,
) -> models.SignalDatasetModel:
    signal_dataset = crud.get_signal_dataset(uuid_)
    signal_dataset = crud.execute_query_one(db, signal_dataset)
    return signal_dataset


@app.get(
    "/json/signal_datasets/{uuid_}/shots",
    description="Get information all shots for a single dataset",
    response_model_exclude_unset=True,
)
def get_shots_for_signal_datasets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    uuid_: uuid.UUID = None,
    params: QueryParams = Depends(),
) -> List[models.ShotModel]:
    # Get signals with given signal name
    signals = crud.get_signals(filters=[f"signal_dataset_uuid$eq{uuid_}"])
    signals = crud.execute_query_all(db, signals)
    shot_ids = [item["shot_id"] for item in signals]

    # Get all shots for those signals
    query = db.query(models.ShotModel)
    query = query.filter(models.ShotModel.shot_id.in_(shot_ids))
    query = crud.apply_parameters(
        query, models.ShotModel, params.fields, params.filters, params.sort
    )

    shots = apply_pagination(request, response, db, query, params)
    shots = crud.execute_query_all(db, shots)
    return shots


@app.get(
    "/json/signal_datasets/{uuid_}/signals",
    description="Get information all signals for a single signal dataset",
    response_model_exclude_unset=True,
)
def get_signals_for_signal_datasets(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    uuid_: uuid.UUID = None,
    params: QueryParams = Depends(),
) -> List[models.SignalModel]:
    params.filters.append(f"signal_dataset_uuid$eq{uuid_}")
    query = crud.get_signals(params.sort, params.fields, params.filters)

    signals = apply_pagination(request, response, db, query, params)
    signals = crud.execute_query_all(db, signals)
    return signals


@app.get("/json/signals/aggregate")
def get_signals_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
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
def get_signal_dataset_for_signal(
    db: Session = Depends(get_db), uuid_: uuid.UUID = None
) -> models.SignalDatasetModel:
    signal = crud.get_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    dataset = crud.get_signal_dataset(signal["signal_dataset_uuid"])
    dataset = crud.execute_query_one(db, dataset)
    return dataset


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
    metadata = crud.get_image_metadata(db)
    return metadata.all()


app.mount("/", StaticFiles(directory="./src/api/static/_build/html", html=True))
app.mount("/data", StaticFiles(directory="data"))
