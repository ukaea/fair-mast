from typing import List, get_type_hints

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.encoders import jsonable_encoder

from sqlalchemy.orm import Session

from strawberry.asgi import GraphQL
from strawberry.fastapi import GraphQLRouter

import json
from . import crud, models, graphql, utils
from .page import MetadataPage
from .utils import InputParams
from .database import SessionLocal, engine, get_db
from pydantic import create_model
from fastapi_pagination import Page, add_pagination
from fastapi_pagination.ext.sqlalchemy import paginate

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="src/api/templates")

graphql_app = GraphQL(graphql.schema)

# Setup FastAPI Application
app = FastAPI()
app.mount("/static", StaticFiles(directory="src/api/static"), name="static")
app.mount("/graphql", graphql_app)
add_pagination(app)


@app.get(
    "/json/shots/",
    description="Get information about experimental shots",
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


# @app.get("/html/shots/", response_class=HTMLResponse)
# def read_shots_html(request: Request, db: Session = Depends(get_db)):
#     shots = crud.get_shots(db=db)
#     return templates.TemplateResponse ~/masr
#         "shots.html",
#         {"request": request, "shots": shots},
#     )
