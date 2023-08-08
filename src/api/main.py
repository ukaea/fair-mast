from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="src/api/static"), name="static")
templates = Jinja2Templates(directory="src/api/templates")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# @app.get("/shots/", response_model=list[schemas.Shots])
# def read_shots(db: Session = Depends(get_db)):
#     shots = crud.get_shots(db)
#     return shots


@app.get("/shots/", response_class=HTMLResponse)
def read_shots_html(request: Request, db: Session = Depends(get_db)):
    shots = crud.get_shots(db=db)
    return templates.TemplateResponse(
        "shots.html",
        {"request": request, "shots": shots},
    )
