import datetime
import io
import json
import os
import re
import uuid
from typing import List, Optional

import pandas as pd
import sqlmodel
import ujson
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_pagination import add_pagination
from fastapi_pagination.cursor import CursorPage
from fastapi_pagination.ext.sqlalchemy import paginate
from keycloak import KeycloakOpenID
from keycloak.exceptions import (
    KeycloakAuthenticationError,
    KeycloakAuthorizationConfigError,
    KeycloakError,
)
from sqlalchemy.orm import Session
from strawberry.asgi import GraphQL
from strawberry.http import GraphQLHTTPResponse
from strawberry.types import ExecutionResult

from . import crud, graphql, models
from .create import upsert
from .database import get_db
from .environment import (
    CLIENT_NAME,
    KEYCLOACK_SERVER_URL,
    KEYCLOAK_CLIENT_SECRET,
    REALM_NAME,
)

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

keycloak_id = KeycloakOpenID(
    server_url=KEYCLOACK_SERVER_URL,
    realm_name=REALM_NAME,
    client_id=CLIENT_NAME,
    client_secret_key=KEYCLOAK_CLIENT_SECRET,
    verify=True,
)
security = HTTPBasic()


def authenticate_user_by_role(credentials: HTTPBasicCredentials = Depends(security)):
    try:
        token = keycloak_id.token(
            username=credentials.username,
            password=credentials.password,
            grant_type="password",
        )

        user_info = keycloak_id.userinfo(token=token["access_token"])
        user_roles = (
            user_info.get("resource_access", {}).get(CLIENT_NAME, {}).get("roles", {})
        )
        if "fair-mast-admins" not in user_roles:
            raise KeycloakAuthorizationConfigError(
                error_message="Forbidden user: Access not sufficient", response_code=403
            )
        return user_info
    except KeycloakAuthenticationError:
        raise KeycloakAuthenticationError(
            error_message="Invalid username or password", response_code=401
        )


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


class CustomJSONResponse(JSONResponse):
    """
    serializes the result of a database query (a dictionary) into a JSON-readable format
    """

    media_type = "application/json"

    def render(self, content) -> bytes:
        """
        renders the output of the request
        """
        content = self.convert_to_jsonld_terms(content)
        extracted_dict = {}
        edited_content = self.extract_meta_key(content, extracted_dict)

        # merge content with extracted context by placing context at the top
        merged_content = {**extracted_dict, **edited_content}

        return json.dumps(merged_content).encode()

    def convert_to_jsonld_terms(self, items):
        """
        Replaces '__' with ':', and [A-Za-z_] with [@A-Za-z] in the mapping of terms (column names) to
        their URIs to ensure the output data conforms with JSON-readable format
        """
        if not isinstance(items, dict):
            return items
        for key, val in list(items.items()):
            # Recursive key modification if value is a dictionary or list object
            if isinstance(val, list):
                items[key] = [self.convert_to_jsonld_terms(item) for item in val]
            if isinstance(val, dict):
                items[key] = self.convert_to_jsonld_terms(val)

            if key.endswith("_"):
                items[f"@{key[:-1]}"] = items.pop(key)
            elif "__" in str(key):
                items[re.sub("__", ":", key)] = items.pop(key)
        return items

    def extract_meta_key(self, content, extracted_dict):
        """
        Extract keys and values of @context and @type from the dictionary to
        return them at the top of the dictionary as one entity for the whole dictionary,
        rather than each for each item since they contain the same key and values
        """
        target_keys = ["@context", "@type", "dct:title"]
        for k, v in list(content.items()):
            if k in target_keys:
                extracted_dict[k] = v
                content.pop(k, None)
            elif isinstance(v, dict):
                # recursive edit_dict call for nested dict
                self.extract_meta_key(v, extracted_dict)
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        self.extract_meta_key(item, extracted_dict)
        # return popped content
        return content


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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
)
def get_shots(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "shot_id"

    query = crud.select_query(
        models.ShotModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.post("/json/shots", description="Post data to shot table")
def post_shots(
    shot_data: list[dict],
    db: Session = Depends(get_db),
    _: HTTPBasicCredentials = Depends(authenticate_user_by_role),
):
    try:
        engine = db.get_bind()
        df = pd.DataFrame(shot_data)
        df.to_sql("shots", engine, if_exists="append", index=False, method=upsert)
        return shot_data
    except Exception as e:
        raise KeycloakError(response_code=400, error_message=f"Error:{str(e)}")


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
    response_class=CustomJSONResponse,
)
def get_shot(db: Session = Depends(get_db), shot_id: int = None):
    shot = crud.get_shot(shot_id)
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/dataservice",
    description="Get information about a the data service this application offers",
    response_class=CustomJSONResponse,
)
def get_dataservice(db: Session = Depends(get_db)):
    dataservices = crud.get_dataservices(db)
    return dataservices


@app.get(
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model=CursorPage[models.SignalModel],
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
)
def get_level2_shot(db: Session = Depends(get_db), shot_id: int = None):
    shot = crud.get_level2_shot(shot_id)
    shot = crud.execute_query_one(db, shot)
    return shot


@app.get(
    "/json/level2/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model=models.Level2SignalModel,
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
)
def get_signals(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "uuid"
    query = crud.select_query(
        models.SignalModel, params.fields, params.filters, params.sort
    )

    return paginate(db, query)


@app.post("/json/signals", description="post data to signal table")
def post_signal(
    signal_data: list[dict],
    db: Session = Depends(get_db),
    _: HTTPBasicCredentials = Depends(authenticate_user_by_role),
):
    try:
        engine = db.get_bind()
        df = pd.DataFrame(signal_data)
        df.to_sql("signals", engine, if_exists="append", index=False, method=upsert)
        return signal_data
    except Exception as e:
        raise KeycloakError(response_code=400, error_message=f"Error:{str(e)}")


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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
)
def get_cpf_summary(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "index"

    query = crud.select_query(
        models.CPFSummaryModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.post("/json/cpf_summary", description="post data to cpf summary table")
def post_cpf_summary(
    cpf_data: list[dict],
    db: Session = Depends(get_db),
    _: HTTPBasicCredentials = Depends(authenticate_user_by_role),
):
    try:
        engine = db.get_bind()
        df = pd.DataFrame(cpf_data)
        df.to_sql("cpf_summary", engine, if_exists="append", index=False, method=upsert)
        return cpf_data
    except Exception as e:
        raise KeycloakError(response_code=400, error_message=f"Error:{str(e)}")


@app.get(
    "/json/scenarios",
    description="Get information on different scenarios.",
    response_model=CursorPage[models.ScenarioModel],
    response_class=CustomJSONResponse,
)
def get_scenarios(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "id"

    query = crud.select_query(
        models.ScenarioModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.post("/json/scenarios", description="post data to scenario table")
def post_scenarios(
    scenario_data: list[dict],
    db: Session = Depends(get_db),
    _: HTTPBasicCredentials = Depends(authenticate_user_by_role),
):
    try:
        engine = db.get_bind()
        df = pd.DataFrame(scenario_data)
        df.to_sql("scenarios", engine, if_exists="append", index=False, method=upsert)
        return scenario_data
    except Exception as e:
        raise KeycloakError(response_code=400, error_message=f"Error:{str(e)}")


@app.get(
    "/json/sources",
    description="Get information on different sources.",
    response_model=CursorPage[models.SourceModel],
    response_class=CustomJSONResponse,
)
def get_sources(db: Session = Depends(get_db), params: QueryParams = Depends()):
    if params.sort is None:
        params.sort = "name"

    query = crud.select_query(
        models.SourceModel, params.fields, params.filters, params.sort
    )
    return paginate(db, query)


@app.post("/json/sources", description="Post Shot data into database")
def post_source(
    source_data: list[dict],
    db: Session = Depends(get_db),
    _: HTTPBasicCredentials = Depends(authenticate_user_by_role),
):
    try:
        engine = db.get_bind()
        df = pd.DataFrame(source_data)
        df.to_sql("sources", engine, if_exists="append", index=False, method=upsert)
        return source_data
    except Exception as e:
        raise KeycloakError(response_code=400, error_message=f"Error:{str(e)}")


@app.get(
    "/json/sources/aggregate",
    response_model=models.SourceModel,
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
)
def get_single_source(db: Session = Depends(get_db), name: str = None):
    source = crud.get_source(db, name)
    source = db.execute(source).one()[0]
    return source


@app.get(
    "/json/level2/sources",
    description="Get information on different sources.",
    response_model=CursorPage[models.Level2SourceModel],
    response_class=CustomJSONResponse,
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
    response_class=CustomJSONResponse,
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


@app.get(
    "/parquet/level2/shots",
    description="Get data on shots as a parquet file",
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
        print(shot_id)
        query = query.where(models.Level2SignalModel.shot_id == shot_id)
    content = query_to_parquet_bytes(db, query)
    return Response(content=content, media_type="application/octet-stream")


@app.get(
    "/parquet/level2/sources",
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
