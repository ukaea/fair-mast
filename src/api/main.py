import datetime
import io
import os
import uuid
from typing import List, Optional

import pandas as pd
import sqlmodel
import ujson
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    Response,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import (
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.orm import Session
from strawberry.asgi import GraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from . import crud, graphql, models
from .database import get_db
from .models import CPFSummaryModel, ScenarioModel, ShotModel, SignalModel, SourceModel

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

DEFAULT_PER_PAGE = 100

# Setup FastAPI Application
app = FastAPI(title="MAST Archive", servers=[{"url": SITE_URL}])
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)
add_pagination(app)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder(
            {
                "Error details": exc.errors(),  # optionally include the errors
                "body": exc.body,
                "message": {
                    "Unprocessable entity. Please check your query and/or filter."
                },
            }
        ),
    )


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


@app.get(
    "/json/shots",
    description="Get information about experimental shots",
)
def get_shots(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> CursorPage[ShotModel]:
    if params.sort is None:
        params.sort = "shot_id"

    query = crud.select_query(ShotModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


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
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
)
def get_signals_for_shot(
    db: Session = Depends(get_db),
    shot_id: int = None,
    params: QueryParams = Depends(),
) -> CursorPage[SignalModel]:
    if params.sort is None:
        params.sort = "uuid"
    # Get shot
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)

    # Get signals for this shot
    params.filters.append(f"shot_id$eq:{shot['shot_id']}")
    query = crud.select_query(SignalModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/signals",
    description="Get information about specific signals.",
)
def get_signals(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> CursorPage[SignalModel]:
    if params.sort is None:
        params.sort = "uuid"

    query = crud.select_query(SignalModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


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
    "/json/cpf_summary",
    description="Get descriptions of CPF summary variables.",
)
def get_cpf_summary(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> CursorPage[CPFSummaryModel]:
    if params.sort is None:
        params.sort = "index"

    query = crud.select_query(
        CPFSummaryModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/scenarios",
    description="Get information on different scenarios.",
)
def get_scenarios(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> CursorPage[ScenarioModel]:
    if params.sort is None:
        params.sort = "id"

    query = crud.select_query(ScenarioModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get(
    "/json/sources",
    description="Get information on different sources.",
)
def get_sources(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> CursorPage[SourceModel]:
    if params.sort is None:
        params.sort = "name"

    query = crud.select_query(SourceModel, params.fields, params.filters, params.sort)
    return paginate(db, query)


@app.get("/json/sources/aggregate")
def get_sources_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
):
    items = query_aggregate(request, response, db, models.SourceModel, params)
    return items


@app.get(
    "/json/sources/{name}",
    description="Get information about a single signal",
)
def get_single_source(
    db: Session = Depends(get_db), name: str = None
) -> models.SourceModel:
    source = crud.get_source(db, name)
    source = db.execute(source).one()[0]
    return source


@app.get(
    "/ndjson/signals",
    description="Get data on signals as an ndjson stream",
)
def get_signals_stream(
    name: Optional[str] = None,
    shot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
) -> models.SignalModel:
    query = crud.select_query(
        models.SignalModel, params.fields, params.filters, params.sort
    )
    if name is None and shot_id is None:
        raise HTTPException(
            status_code=400, detail="Must provide one of a shot_id or a signal name."
        )
    if name is not None:
        query = query.where(models.SignalModel.name == name)
    if shot_id is not None:
        query = query.where(models.SignalModel.shot_id == shot_id)
    stream = ndjson_stream_query(db, query)
    return StreamingResponse(stream, media_type="application/x-ndjson")


@app.get(
    "/ndjson/shots",
    description="Get data on shots as an ndjson stream",
)
def get_shots_stream(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> models.ShotModel:
    query = crud.select_query(
        models.ShotModel, params.fields, params.filters, params.sort
    )
    stream = ndjson_stream_query(db, query)
    return StreamingResponse(stream, media_type="application/x-ndjson")


@app.get(
    "/ndjson/sources",
    description="Get data on sources as an ndjson stream",
)
def get_sources_stream(
    db: Session = Depends(get_db), params: QueryParams = Depends()
) -> models.SourceModel:
    query = crud.select_query(
        models.SourceModel, params.fields, params.filters, params.sort
    )
    stream = ndjson_stream_query(db, query)
    return StreamingResponse(stream, media_type="application/x-ndjson")


def ndjson_stream_query(db, query):
    STREAM_SIZE = 1000
    offset = 0
    more_results = True
    while more_results:
        q = query.limit(STREAM_SIZE).offset(offset)
        results = db.execute(q)
        results = [r[0] for r in results.all()]
        outputs = [item.dict(exclude_none=True) for item in results]
        for item in outputs:
            for k, v in item.items():
                if isinstance(v, uuid.UUID):
                    item[k] = str(v)
                elif isinstance(v, datetime.datetime):
                    item[k] = str(v)
                elif isinstance(v, datetime.time):
                    item[k] = str(v)

        outputs = [ujson.dumps(item) + "\n" for item in outputs]
        outputs = "".join(outputs)
        yield outputs
        more_results = len(results) > 0
        offset += STREAM_SIZE


@app.get(
    "/parquet/shots",
    description="Get data on shots as a parquet file",
)
def get_parquet_shots(
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.ShotModel, params.fields, params.filters, params.sort
    )
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/parquet/signals",
    description="Get data on signals as a parquet stream",
)
def get_parquet_signals(
    name: Optional[str] = None,
    shot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.SignalModel, params.fields, params.filters, params.sort
    )
    if name is None and shot_id is None:
        raise HTTPException(
            status_code=400, detail="Must provide one of a shot_id or a signal name."
        )
    if name is not None:
        query = query.where(models.SignalModel.name == name)
    if shot_id is not None:
        query = query.where(models.SignalModel.shot_id == shot_id)
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/parquet/sources",
    description="Get data on sources as a parquet file",
)
def get_parquet_sources(
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.SourceModel, params.fields, params.filters, params.sort
    )
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


def query_to_parquet_bytes(db, query) -> bytes:
    df = pd.read_sql(query, con=db.connection())
    if "uuid" in df:
        df["uuid"] = df["uuid"].map(str)

    buffer = io.BytesIO()
    df.to_parquet(buffer)
    buffer.seek(0)
    content = buffer.read()
    return content


app.mount("/intake", StaticFiles(directory="./src/api/static/intake"))
app.mount("/", StaticFiles(directory="./src/api/static/_build/html", html=True))
