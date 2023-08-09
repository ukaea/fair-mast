from sqlalchemy.orm import Session

from . import models


def get_shots(db: Session):
    return get_shots_stream(db).all()


def get_shots_stream(db: Session):
    return db.query(models.ShotModel).order_by(models.ShotModel.shot_id.desc())
