import io
from sqlalchemy.orm import Session
import pandas as pd
import uuid
from . import models
from fastapi.responses import StreamingResponse
from .database import engine


MEDIA_TYPES = {
    "parquet": "binary",
    "csv": "text",
}

DF_EXPORT_FUNCS = {
    "parquet": lambda df, stream: df.to_parquet(stream),
    "csv": lambda df, stream: df.to_csv(stream),
}


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


def get_shot(db: Session, shot_id: int):
    query = db.query(models.ShotModel)
    query = query.filter(models.ShotModel.shot_id == shot_id)
    return query


def get_signal_datasets(db: Session, params):
    query = db.query(models.SignalDatasetModel)
    query = do_where(models.SignalDatasetModel, query, params)
    query = query.order_by(models.SignalDatasetModel.signal_dataset_id.desc())
    return query


def get_signal_dataset(db: Session, name: str):
    query = db.query(models.SignalDatasetModel)
    query = query.filter(models.SignalDatasetModel.name == name)
    return query


def get_signals(db: Session, params):
    query = db.query(models.SignalModel)
    query = do_where(models.SignalModel, query, params)
    query = query.order_by(models.SignalModel.id.desc())
    return query


def get_signal(db: Session, name: str):
    query = db.query(models.SignalModel)
    query = query.filter(models.SignalModel.name == name)
    return query


def get_cpf_summary(db: Session):
    query = db.query(models.CPFSummaryModel)
    query = query.order_by(models.CPFSummaryModel.name)
    return query


def get_scenarios(db: Session):
    query = db.query(models.ScenarioModel)
    query = query.order_by(models.ScenarioModel.name)
    return query


def get_sources(db: Session):
    query = db.query(models.SourceModel)
    query = query.order_by(models.SourceModel.name)
    return query


def get_source(db: Session, name: str):
    query = db.query(models.SourceModel)
    query = query.filter(models.SourceModel.name == name)
    return query


def get_image_metdata(db: Session):
    query = db.query(models.ImageMetadataModel)
    query = query.order_by(models.ImageMetadataModel.name)
    return query


def get_table_as_dataframe(query, name: str, ext: str = "parquet"):
    if ext not in MEDIA_TYPES:
        raise RuntimeError(f"Unknown extension type {ext}")

    media_type = MEDIA_TYPES[ext]

    df = pd.read_sql(query.statement, con=engine.connect())
    columns = df.columns
    for column in columns:
        if df[column].dtype == uuid.UUID:
            df[column] = df[column].astype(str)

    stream = io.BytesIO() if media_type == "binary" else io.StringIO()
    DF_EXPORT_FUNCS[ext](df, stream)

    response = StreamingResponse(
        iter([stream.getvalue()]), media_type=f"{media_type}/{ext}"
    )
    response.headers["Content-Disposition"] = f"attachment; filename={name}.{ext}"
    return response
