from typing import Any, List

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

import strawberry
from strawberry.asgi import GraphQL
from strawberry.fastapi import GraphQLRouter

import json
import ndjson
from . import crud, models, graphql
from .database import SessionLocal, engine, get_db

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="src/api/templates")


graphql_app = GraphQL(graphql.schema)

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/api/static"), name="static")
app.mount("/graphql", graphql_app)


@app.get(
    "/json/shots/", response_model=list[models.ShotModel], response_class=JSONResponse
)
def read_shots_json(db: Session = Depends(get_db)):
    shots = crud.get_shots(db)
    return shots


async def shots_streamer(db: Session):
    shots = crud.get_shots_stream(db)
    for shot in shots:
        item = schemas.Shot.from_orm(shot)
        payload = json.dumps(
            jsonable_encoder(item),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        )
        yield f"{payload}\n"


async def shot_signal_link_streamer(db: Session):
    shot_signal_links = crud.get_shot_signal_link_stream(db)
    for shot_signal_link in shot_signal_links:
        item = schemas.ShotSignalLink.from_orm(shot_signal_link)
        payload = json.dumps(
            jsonable_encoder(item),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        )
        yield f"{payload}\n"


@app.head("/ndjson/shot_signal_link/")
@app.get("/ndjson/shot_signal_link/", response_class=StreamingResponse)
async def read_shot_signal_link_ndjson(db: Session = Depends(get_db)):
    size = crud.get_shot_signal_link_size()
    shot_signal_link = shot_signal_link_streamer(db)
    return StreamingResponse(shot_signal_link)


@app.get("/ndjson/shots/", response_class=StreamingResponse)
async def read_shots_ndjson(db: Session = Depends(get_db)):
    shots = shots_streamer(db)
    return StreamingResponse(shots)


@app.get("/html/shots/", response_class=HTMLResponse)
def read_shots_html(request: Request, db: Session = Depends(get_db)):
    shots = crud.get_shots(db=db)
    return templates.TemplateResponse(
        "shots.html",
        {"request": request, "shots": shots},
    )
