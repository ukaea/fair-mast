from sqlalchemy.orm import Session

from . import models, schemas


def get_shots(db: Session):
    return db.query(models.Shots).limit(100).all()
