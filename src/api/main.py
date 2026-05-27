import datetime
import io
import json
import os
import uuid
from pathlib import Path
from typing import List, Optional

import pandas as pd
import sqlmodel
import ujson
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import paginate
from rdflib import Graph
from sqlalchemy.orm import Session
from strawberry.asgi import GraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from . import crud, graphql, models, utils
from .database import get_db
from .environment import LICENSE_URL, SITE_URL

templates = Jinja2Templates(directory="src/api/templates")

_SKIP_KEYS = {"context_", "type_", "@context", "@type", "@id"}

_DATASET_TERMS = {
    "uuid": "dct:identifier",
    "timestamp": "dct:date",
    "description": "dct:description",
    "source": "dct:source",
    "title": "dct:title",
    "name": "schema:name",
    "version": "schema:version",
}

_DEFINED_TERM_TERMS = {
    "name": "schema:name",
    "description": "dct:description",
}

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


def _context_for(node, terms: Optional[dict] = None) -> dict:
    """Minimal ``@context`` for a rendered node"""
    g = Graph()
    utils.bind_base_namespaces(g)
    prefixes = {p: str(n) for p, n in g.namespace_manager.namespaces()}
    used_prefixes: set = set()
    used_terms: dict = {}

    def walk(v):
        if isinstance(v, dict):
            for k, val in v.items():
                if ":" in k and not k.startswith("@") and k.split(":", 1)[0] in prefixes:
                    used_prefixes.add(k.split(":", 1)[0])
                if terms and k in terms:
                    used_terms[k] = terms[k]
                    prefix = terms[k].split(":", 1)[0]
                    if prefix in prefixes:
                        used_prefixes.add(prefix)
                walk(val)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and ":" in v and v.split(":", 1)[0] in prefixes:
            used_prefixes.add(v.split(":", 1)[0])

    walk(node)
    context = {p: prefixes[p] for p in sorted(used_prefixes)}
    context.update(used_terms)
    return context


def _distribution(item) -> Optional[dict]:
    """Build a ``dcat:Distribution`` from ``url`` / ``endpoint_url`` if
    the record carries an ``s3://`` URL with an HTTP endpoint."""
    s3_url = item.get("url")
    endpoint = item.get("endpoint_url")
    if not (isinstance(s3_url, str) and s3_url.startswith("s3://") and endpoint):
        return None
    return {
        "@type": "dcat:Distribution",
        "dcat:accessURL": SITE_URL,
        "dcat:downloadURL": f"{endpoint.rstrip('/')}/{s3_url[len('s3://'):]}",
        "dcat:mediaType": "application/zarr",
        "dct:license": LICENSE_URL,
    }


def _dataset_node(item) -> dict:
    """Render a record as a ``dcat:Dataset`` body. Column names stay
    as-is (``description``, ``uuid``, ``shot_id``, ...); the response
    class's ``@context`` maps the ones with RDF semantics to their
    predicates."""
    distribution = _distribution(item)
    if distribution is not None:
        item = {k: v for k, v in item.items() if k not in ("url", "endpoint_url")}
    node: dict = {"@type": "dcat:Dataset"}
    for k, v in item.items():
        if k in _SKIP_KEYS:
            continue
        node[k] = v
    if distribution is not None:
        node["dcat:distribution"] = distribution
    return node


def _defined_term_node(item) -> dict:
    node: dict = {"@type": "schema:DefinedTerm"}
    for k, v in item.items():
        if k in _SKIP_KEYS:
            continue
        node[k] = v
    return node


def _rewrite_key(key: str) -> str:
    if key.startswith("@"):
        return key
    if key.endswith("_") and "__" not in key:
        return f"@{key[:-1]}"
    if "__" in key:
        return key.replace("__", ":", 1)
    return key


def _rewrite(value):
    """Apply ``_rewrite_key`` recursively through a dict / list tree."""
    if isinstance(value, dict):
        return {_rewrite_key(k): _rewrite(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_rewrite(v) for v in value]
    return value


def _render(body: dict, terms: Optional[dict] = None, wrapper: Optional[dict] = None) -> bytes:
    """Prepend a @context fold in any wrapper keys (e.g. pagination metadata), and
    dump to JSON."""
    result = {"@context": _context_for(body, terms), **body}
    if wrapper:
        result.update(wrapper)
    return json.dumps(result, default=str).encode()


class DatasetResponse(JSONResponse):
    """A single ``dcat:Dataset`` record."""

    media_type = "application/json"

    def render(self, content) -> bytes:
        return _render(_dataset_node(content), _DATASET_TERMS)


class CatalogResponse(JSONResponse):
    """A paginated listing as a dcat:Catalog of datasets"""

    media_type = "application/json"

    def render(self, content) -> bytes:
        items = content.get("items", [])
        wrapper = {k: v for k, v in content.items() if k != "items"}
        catalog = {
            "@type": "dcat:Catalog",
            "items": [_dataset_node(item) for item in items],
        }
        terms = {**_DATASET_TERMS, "items": "dcat:dataset"}
        return _render(catalog, terms, wrapper)


class DefinedTermSetResponse(JSONResponse):
    """A paginated glossary as a schema:DefinedTermSet of schema:DefinedTerm entries."""

    media_type = "application/json"

    def render(self, content) -> bytes:
        items = content.get("items", [])
        wrapper = {k: v for k, v in content.items() if k != "items"}
        term_set = {
            "@type": "schema:DefinedTermSet",
            "items": [_defined_term_node(item) for item in items],
        }
        terms = {**_DEFINED_TERM_TERMS, "items": "schema:hasDefinedTerm"}
        return _render(term_set, terms, wrapper)


class DataServiceResponse(JSONResponse):
    """The data service description as a dcat:DataService"""

    media_type = "application/json"

    def render(self, content) -> bytes:
        return json.dumps(_rewrite(content), default=str).encode()


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
    "/json",
    description="Root of JSON API - shows available endpoints.",
)
def json_root():
    return {
        "message": "Welcome to the FAIR MAST API.",
        "documentation_url": "https://mastapp.site/redoc",
        "example_endpoints": [
            "/json/shots",
            "/json/cpf_summary",
            "/json/scenarios",
            "/json/sources",
        ],
    }


@app.get(
    "/json/shots",
    description="Get information about experimental shots",
    response_model=CursorPage[models.ShotModel],
    response_class=CatalogResponse,
)
def get_shots(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "shot_id"

    query = crud.select_query(
        models.ShotModel, params.fields, params.filters, params.sort
    )
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
    response_model=models.ShotModel,
    response_class=DatasetResponse,
)
def get_shot(db: Session = Depends(get_db), shot_id: int = None):
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/dataservice",
    description="Get information about a the data service this application offers",
    response_class=DataServiceResponse,
)
def get_dataservice(db: Session = Depends(get_db)):
    dataservices = crud.get_dataservices(db)
    return dataservices


@app.get(
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model=CursorPage[models.SignalModel],
    response_class=CatalogResponse,
)
def get_signals_for_shot(
    db: Session = Depends(get_db),
    shot_id: int = None,
    params: QueryParams = Depends(),
):
    if params.sort is None:
        params.sort = "uuid"
    # Get shot
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)

    # Get signals for this shot
    params.filters.append(f"shot_id$eq:{shot['shot_id']}")
    query = crud.select_query(
        models.SignalModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/level2/shots",
    description="Get information about experimental shots",
    response_model=CursorPage[models.Level2ShotModel],
    response_class=CatalogResponse,
)
def get_level2_shots(
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    if params.sort is None:
        params.sort = "shot_id"

    query = crud.select_query(
        models.Level2ShotModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get("/json/level2/shots/aggregate")
def get_level2_shots_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
):
    items = query_aggregate(request, response, db, models.Level2ShotModel, params)
    return items


@app.get(
    "/json/level2/shots/{shot_id}",
    description="Get information about a single experimental shot",
    response_model=models.Level2ShotModel,
    response_class=DatasetResponse,
)
def get_level2_shot(db: Session = Depends(get_db), shot_id: int = None):
    shot = crud.get_level2_shot(shot_id)
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/level2/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model=models.Level2SignalModel,
    response_class=CatalogResponse,
)
def get_signals_for_level2_shot(
    db: Session = Depends(get_db),
    shot_id: int = None,
    params: QueryParams = Depends(),
):
    if params.sort is None:
        params.sort = "uuid"
    # Get shot
    shot = crud.get_level2_shot(shot_id)
    shot = crud.execute_query_one(db, shot)

    # Get signals for this shot
    params.filters.append(f"shot_id$eq:{shot['shot_id']}")
    query = crud.select_query(
        models.Level2SignalModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/signals",
    description="Get information about specific signals.",
    response_model=CursorPage[models.SignalModel],
    response_class=CatalogResponse,
)
def get_signals(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "uuid"
    query = crud.select_query(
        models.SignalModel, params.fields, params.filters, params.sort
    )

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
    response_model=models.SignalModel,
    response_class=DatasetResponse,
)
def get_signal(db: Session = Depends(get_db), uuid_: uuid.UUID = None):
    signal = crud.get_signal(uuid_)
    signal = crud.execute_query_one(db, signal)

    return signal


@app.get(
    "/json/signals/{uuid_}/shot",
    description="Get information about the shot for a single signal",
    response_model_exclude_unset=True,
    response_model=models.ShotModel,
    response_class=DatasetResponse,
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
    "/json/level2/signals",
    description="Get information about specific signals.",
    response_model=CursorPage[models.Level2SignalModel],
    response_class=CatalogResponse,
)
def get_level2_signals(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "uuid"

    query = crud.select_query(
        models.Level2SignalModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get("/json/level2/signals/aggregate")
def get_level2_signals_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
):
    items = query_aggregate(request, response, db, models.Level2SignalModel, params)
    return items


@app.get(
    "/json/level2/signals/{uuid_}",
    description="Get information about a single signal",
    response_model_exclude_unset=True,
    response_model=models.Level2SignalModel,
    response_class=DatasetResponse,
)
def get_level2_signal(db: Session = Depends(get_db), uuid_: uuid.UUID = None):
    signal = crud.get_level2_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    return signal


@app.get(
    "/json/level2/signals/{uuid_}/shot",
    description="Get information about the shot for a single signal",
    response_model_exclude_unset=True,
    response_model=models.Level2ShotModel,
    response_class=DatasetResponse,
)
def get_shot_for_level2_signal(db: Session = Depends(get_db), uuid_: uuid.UUID = None):
    signal = crud.get_level2_signal(uuid_)
    signal = crud.execute_query_one(db, signal)
    shot = crud.get_level2_shot(signal["shot_id"])
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/cpf_summary",
    description="Get descriptions of CPF summary variables.",
    response_model=CursorPage[models.CPFSummaryModel],
    response_class=DefinedTermSetResponse,
)
def get_cpf_summary(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "index"

    query = crud.select_query(
        models.CPFSummaryModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/scenarios",
    description="Get information on different scenarios.",
    response_model=CursorPage[models.ScenarioModel],
    response_class=DefinedTermSetResponse,
)
def get_scenarios(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "id"

    query = crud.select_query(
        models.ScenarioModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/sources",
    description="Get information on different sources.",
    response_model=CursorPage[models.SourceModel],
    response_class=CatalogResponse,
)
def get_sources(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "name"

    query = crud.select_query(
        models.SourceModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get(
    "/json/sources/aggregate",
    response_model=models.SourceModel,
)
def get_sources_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
) -> models.SourceModel:
    items = query_aggregate(request, response, db, models.SourceModel, params)
    return items


@app.get(
    "/json/sources/{name}",
    description="Get information about a single signal",
    response_model=models.SourceModel,
    response_class=DatasetResponse,
)
def get_single_source(db: Session = Depends(get_db), name: str = None):
    source = crud.get_source(db, name)
    source = db.execute(source).one()[0]
    return source


@app.get(
    "/json/level2/sources",
    description="Get information on different sources.",
    response_model=CursorPage[models.Level2SourceModel],
    response_class=CatalogResponse,
)
def get_level2_sources(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "name"

    query = crud.select_query(
        models.Level2SourceModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.get("/json/level2/sources/aggregate")
def get_level2_sources_aggregate(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    params: AggregateQueryParams = Depends(),
):
    items = query_aggregate(request, response, db, models.Level2SourceModel, params)
    return items


@app.get(
    "/json/level2/sources/{uuid_}",
    description="Get information about a single signal",
    response_model=models.Level2SourceModel,
    response_class=DatasetResponse,
)
def get_level2_single_source(db: Session = Depends(get_db), uuid_: uuid.UUID = None):
    source = crud.get_level2_source(db, uuid_)
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
@app.get("/parquet/shots.parquet", description="Get data on shots as a parquet file")
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
@app.get(
    "/parquet/signals.parquet", description="Get data on signals as a parquet file"
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
@app.get(
    "/parquet/sources.parquet", description="Get data on sources as a parquet file"
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


@app.get(
    "/parquet/level2/shots",
    description="Get data on shots as a parquet file",
)
@app.get(
    "/parquet/level2/shots.parquet", description="Get data on shots as a parquet file"
)
def get_parquet_level2_shots(
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.Level2ShotModel, params.fields, params.filters, params.sort
    )
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/parquet/level2/signals",
    description="Get data on signals as a parquet stream",
)
@app.get(
    "/parquet/level2/signals.parquet",
    description="Get data on signals as a parquet file",
)
def get_parquet_level2_signals(
    name: Optional[str] = None,
    shot_id: Optional[int] = None,
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.Level2SignalModel, params.fields, params.filters, params.sort
    )
    if name is None and shot_id is None:
        raise HTTPException(
            status_code=400, detail="Must provide one of a shot_id or a signal name."
        )
    if name is not None:
        query = query.where(models.Level2SignalModel.name == name)
    if shot_id is not None:
        query = query.where(models.Level2SignalModel.shot_id == shot_id)
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/parquet/level2/sources",
    description="Get data on sources as a parquet file",
)
@app.get(
    "/parquet/level2/sources.parquet",
    description="Get data on sources as a parquet file",
)
def get_parquet_level2_sources(
    db: Session = Depends(get_db),
    params: QueryParams = Depends(),
):
    query = crud.select_query(
        models.Level2SourceModel, params.fields, params.filters, params.sort
    )
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


def query_to_parquet_bytes(db: Session, query: Query) -> bytes:
    items = db.scalars(query)
    df = pd.DataFrame([item.dict(exclude_none=True, by_alias=True) for item in items])

    if "uuid" in df:
        df["uuid"] = df["uuid"].map(str)

    # ensure shot_id is the first column if present
    if "shot_id" in df:
        col = df.pop("shot_id")
        df.insert(0, "shot_id", col)

    buffer = io.BytesIO()
    df.to_parquet(buffer)
    buffer.seek(0)
    content = buffer.read()
    return content


docs_built = Path("./docs/built")
docs_default = Path("./docs/default")
docs_built.mkdir(parents=True, exist_ok=True)
docs_default.mkdir(parents=True, exist_ok=True)

if len(list(docs_built.iterdir())) > 1:
    docs_directory = "./docs/built/_build/html"
else:
    docs_directory = "./docs/default"

app.mount("/", StaticFiles(directory=docs_directory, html=True))
