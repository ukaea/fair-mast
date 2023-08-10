from sqlalchemy.orm import Session

from . import models


def do_where(cls_, query, params):
    """Apply a where clause with the InputParams"""
    for name, value in params:
        if value is not None:
            query = query.filter(getattr(cls_, name) == value)
    return query


def get_shots(db: Session, params):
    query = db.query(models.ShotModel)
    query = do_where(models.ShotModel, query, params)
    query = query.order_by(models.ShotModel.shot_id.desc())
    return query


def get_signals(db: Session, params):
    query = db.query(models.SignalModel)
    query = do_where(models.SignalModel, query, params)
    query = query.order_by(models.SignalModel.signal_id.desc())
    return query


def get_shots_stream(db: Session):
    return db.query(models.ShotModel).order_by(models.ShotModel.shot_id.desc())
