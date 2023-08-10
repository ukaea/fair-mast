import typing as t
from typing import Any, List, get_type_hints

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
    "/json/signals/",
    description="Get information about different signals from diagnostic equipment.",
)
def read_signals_json(
    db: Session = Depends(get_db),
    params: InputParams(models.SignalModel) = Depends(),
) -> MetadataPage[models.SignalModel]:
    signals = crud.get_signals(db, params)
    metadata = utils.create_model_column_metadata(models.SignalModel)
    return paginate(db, signals, additional_data={"column_metadata": metadata})


# @app.get("/html/shots/", response_class=HTMLResponse)
# def read_shots_html(request: Request, db: Session = Depends(get_db)):
#     shots = crud.get_shots(db=db)
#     return templates.TemplateResponse(
#         "shots.html",
#         {"request": request, "shots": shots},
#     )
