import h5py
from typing import List, get_type_hints

from fastapi import (
    Depends,
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

add_pagination(app)


@app.get(
    "/json/shots/",
    description="Get information about experimental shots",
    response_model=MetadataPage[models.ShotModel],
)
def read_shots_json(
    db: Session = Depends(get_db),
    params: InputParams(models.ShotModel) = Depends(),
) -> MetadataPage[models.ShotModel]:
    shots = crud.get_shots(db, params)
    metadata = utils.create_model_column_metadata(models.ShotModel)
    return paginate(db, shots, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signal_datasets/",
    description="Get information about different signal datasets.",
)
def read_signal_datasets_json(
    db: Session = Depends(get_db),
    params: InputParams(models.SignalDatasetModel) = Depends(),
) -> MetadataPage[models.SignalDatasetModel]:
    signals = crud.get_signal_datasets(db, params)
    metadata = utils.create_model_column_metadata(models.SignalDatasetModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


@app.get(
    "/json/signals/",
    description="Get information about specific signals.",
)
def read_signals_json(
    db: Session = Depends(get_db),
    params: InputParams(models.SignalModel) = Depends(),
) -> MetadataPage[models.SignalModel]:
    signals = crud.get_signals(db, params)
    metadata = utils.create_model_column_metadata(models.SignalModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


@app.get(
    "/json/cpf_summary/",
    description="Get descriptions of CPF summary variables.",
)
def read_cpf_summary_json(
    db: Session = Depends(get_db),
) -> List[models.CPFSummaryModel]:
    summary = crud.get_cpf_summary(db)
    return summary.all()


@app.get(
    "/json/scenarios/",
    description="Get information on different scenarios.",
)
def read_scenarios_json(
    db: Session = Depends(get_db),
) -> List[models.ScenarioModel]:
    scenarios = crud.get_scenarios(db)
    return scenarios.all()


@app.get(
    "/json/sources",
    description="Get information on different sources.",
)
def read_sources_json(
    db: Session = Depends(get_db),
) -> List[models.SourceModel]:
    sources = crud.get_sources(db)
    return sources.all()


@app.get(
    "/json/image_metadata",
    description="Get image metadata from signals.",
)
def read_image_metadata_json(
    db: Session = Depends(get_db),
) -> List[models.ImageMetadataModel]:
    sources = crud.get_image_metadata(db)
    return sources.all()


@app.get(
    "/meta_catalog.yml",
    description="Get the meta data catalog.",
)
def read_meta_catalog(db: Session = Depends(get_db)) -> FileResponse:
    return FileResponse("data/meta.yml")


@app.get(
    "/files/shots",
    description="Get a file of shot information.",
)
def read_shots_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.ShotModel)
    query = query.order_by(models.ShotModel.shot_id.desc())
    return crud.get_table_as_dataframe(query, "shots", format)


@app.get(
    "/files/signal_datasets",
    description="Get a file of signal dataset information.",
)
def read_signal_datasets_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SignalDatasetModel)
    query = query.order_by(models.SignalDatasetModel.signal_dataset_id)
    return crud.get_table_as_dataframe(query, "signal_datasets", format)


@app.get(
    "/files/signals",
    description="Get a file of signal information.",
)
def read_signals_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SignalModel)
    query = query.order_by(models.SignalModel.id)
    return crud.get_table_as_dataframe(query, "signals", format)


@app.get(
    "/files/scenarios",
    description="Get a file of scenarios information.",
)
def read_scenarios_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.id)
    return crud.get_table_as_dataframe(query, "scenarios", format)


@app.get(
    "/files/sources",
    description="Get a file of sources information.",
)
def read_sources_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.SourceModel)
    query = query.order_by(models.SourceModel.name)
    return crud.get_table_as_dataframe(query, "sources", format)


@app.get(
    "/files/cpf_summary",
    description="Get a file of CPF summary information.",
)
def read_cpf_summary_file(
    db: Session = Depends(get_db), format: FileType = FileType.parquet
) -> StreamingResponse:
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.index)
    return crud.get_table_as_dataframe(query, "cpf_summary", format)
