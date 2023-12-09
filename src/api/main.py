import h5py
from typing import List, get_type_hints, Annotated

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
app = FastAPI(title="MAST Archive")
app.mount("/html", StaticFiles(directory="./src/api/static/html"))
app.mount("/data", StaticFiles(directory="data"))
app.add_route("/graphql", graphql_app)
app.add_websocket_route("/graphql", graphql_app)


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
    fields: str = None,
    filters: str = None,
    sort: str = None,
    page: int = 0,
    per_page: int = 50,
) -> List[models.ShotModel]:
    query = crud.get_shots(sort, fields, filters)
    headers = crud.get_pagination_metadata(db, query, page, per_page, request.url)
    response.headers.update(headers)

    print(dir(request), request.url)
    if request.method == "HEAD":
        return []

    query = crud.apply_pagination(query, page, per_page)
    shots = db.execute(query).all()
    shots = [shot[0].dict(exclude_none=True) for shot in shots]

    return shots


@app.get("/json/shots/aggregate")
def get_shots_aggregate(
    db: Session = Depends(get_db),
    data: str = None,
    groupby: str = None,
    filters: str = None,
    sort: str = None,
):
    query = crud.get_shot_aggregate(data, groupby, filters, sort)
    shots = db.execute(query).all()
    return shots


@app.get(
    "/json/shots/{shot_id}",
    description="Get information about a single experimental shot",
)
def get_shot(db: Session = Depends(get_db), shot_id: int = None) -> models.ShotModel:
    shot = crud.get_shot(db, shot_id)
    shot = db.execute(shot).one()[0]
    return shot


@app.get(
    "/json/shots/{shot_id}/signals",
    description="Get information all signals for a single experimental shot",
    response_model=MetadataPage[models.SignalModel],
)
def get_shot_signals(
    db: Session = Depends(get_db), shot_id: int = None
) -> MetadataPage[models.SignalModel]:
    shot = crud.get_shot(db, shot_id)
    shot = db.execute(shot).one()[0]
    params = InputParams(models.SignalModel)(shot_id=shot_id)
    signals = crud.get_signals(db, params)
    metadata = utils.create_model_column_metadata(models.SignalModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


@app.get(
    "/json/shots/{shot_id}/signal_datasets",
    description="Get information all signal datasts for a single shot",
)
def get_signal_datasets_shots(
    db: Session = Depends(get_db), shot_id: int = None
) -> MetadataPage[models.SignalDatasetModel]:
    params = InputParams(models.SignalModel)(shot_id=shot_id)
    signals = crud.get_signals(db, params)
    signals = db.execute(signals).all()
    signal_names = [item[0].signal_name for item in signals]

    query = db.query(models.SignalDatasetModel)
    query = query.filter(models.SignalDatasetModel.name.in_(signal_names))

    metadata = utils.create_model_column_metadata(models.SignalDatasetModel)
    return paginate(db, query, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signal_datasets/",
    description="Get information about different signal datasets.",
)
def get_signal_datasets(
    db: Session = Depends(get_db),
    params: InputParams(models.SignalDatasetModel) = Depends(),
) -> MetadataPage[models.SignalDatasetModel]:
    signals = crud.get_signal_datasets(db, params)
    metadata = utils.create_model_column_metadata(models.SignalDatasetModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signal_datasets/{name}",
    description="Get information about a single signal dataset",
)
def get_signal_dataset(
    db: Session = Depends(get_db), name: str = None
) -> models.SignalDatasetModel:
    signal_dataset = crud.get_signal_dataset(db, name)
    signal_dataset = db.execute(signal_dataset).one()[0]
    return signal_dataset


@app.get(
    "/json/signal_datasets/{name}/shots",
    description="Get information all shots for a single signal dataset",
    response_model=MetadataPage[models.ShotModel],
)
def get_signal_datasets_shots(
    db: Session = Depends(get_db), name: str = None
) -> MetadataPage[models.ShotModel]:
    params = InputParams(models.SignalModel)(signal_name=name)
    signals = crud.get_signals(db, params)
    signals = db.execute(signals).all()
    shot_ids = [item[0].shot_id for item in signals]

    query = db.query(models.ShotModel)
    query = query.filter(models.ShotModel.shot_id.in_(shot_ids))

    metadata = utils.create_model_column_metadata(models.ShotModel)
    return paginate(db, query, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signal_datasets/{name}/signals",
    description="Get information all signals for a single signal dataset",
)
def get_signal_datasets_shots(
    db: Session = Depends(get_db), name: str = None
) -> MetadataPage[models.SignalModel]:
    params = InputParams(models.SignalModel)(signal_name=name)
    query = crud.get_signals(db, params)
    metadata = utils.create_model_column_metadata(models.SignalModel)
    return paginate(db, query, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signals/",
    description="Get information about specific signals.",
)
def get_signals(
    db: Session = Depends(get_db),
    params: InputParams(models.SignalModel) = Depends(),
) -> MetadataPage[models.SignalModel]:
    signals = crud.get_signals(db, params)
    metadata = utils.create_model_column_metadata(models.SignalModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signals/{signal_name:path}",
    description="Get information about a single signal",
    response_model=models.SignalModel,
)
def get_signal(
    db: Session = Depends(get_db), signal_name: str = None
) -> models.SignalModel:
    signal = crud.get_signal(db, signal_name)
    signal = db.execute(signal).one()[0]
    return signal


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
