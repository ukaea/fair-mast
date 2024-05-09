import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from src.api.main import app
from src.api.database import get_db, Base
from src.api.models import SignalModel, SourceModel
import os
from sqlmodel import Field, Session, SQLModel, create_engine
from src.api.create import DBCreationClient, get_dataset_item_uuid, get_dataset_uuid, read_cpf_metadata, lookup_status_code
from pathlib import Path
from sqlalchemy_utils.functions import (
    drop_database,
    database_exists,
    create_database,
)
from pathlib import Path
from tqdm import tqdm

LAST_MAST_SHOT = 30471

def create_cpf_summary(url, data_path: Path):
    paths = data_path.glob("*_cpf_columns.parquet")
    for path in paths:
            df = pd.read_parquet(path)
            df.to_sql("cpf_summary", url, if_exists="replace")


def create_scenarios(url, data_path: Path):
    """Create the scenarios metadata table"""
    shot_file_name = data_path.parent / "shot_metadata.parquet"
    shot_metadata = pd.read_parquet(shot_file_name)
    ids = shot_metadata["scenario_id"].unique()
    scenarios = shot_metadata["scenario"].unique()
    data = pd.DataFrame(dict(id=ids, name=scenarios)).set_index("id")
    data = data.dropna()
    data.to_sql("scenarios", url, if_exists="append")


def create_shots(url, data_path: Path):
    """Create the shot metadata table"""
    shot_file_name = data_path.parent / "shot_metadata.parquet"
    shot_metadata = pd.read_parquet(shot_file_name)
    shot_metadata = shot_metadata.loc[shot_metadata["shot_id"] <= LAST_MAST_SHOT]
    shot_metadata["facility"] = "MAST"
    shot_metadata = shot_metadata.set_index("shot_id", drop=True)
    shot_metadata = shot_metadata.sort_index()
    shot_metadata["scenario"] = shot_metadata["scenario_id"]
    shot_metadata = shot_metadata.drop(["scenario_id", "reference_id"], axis=1)
    shot_metadata["uuid"] = shot_metadata.index.map(get_dataset_uuid)
    shot_metadata["url"] = (
        f"s3://mast/shots/"
        + shot_metadata["campaign"]
        + "/"
        + shot_metadata.index.astype(str)
        + ".zarr"
    )
    paths = data_path.glob("*_cpf_data.parquet")
    cpfs = []
    for path in paths:
        cpf_metadata = read_cpf_metadata(path)
        cpf_metadata = cpf_metadata.set_index("shot_id", drop=True)
        cpf_metadata = cpf_metadata.sort_index()
        cpfs.append(cpf_metadata)
    cpfs = pd.concat(cpfs, axis=0)
    shot_metadata = pd.merge(
        shot_metadata,
        cpfs,
        left_on="shot_id",
        right_on="shot_id",
        how="inner",
    )
    shot_metadata.to_sql("shots", url, if_exists="append")

def create_signals(url, data_path: Path, num_signals: int):
    file_names = data_path.glob("signals/**/*.parquet")
    file_names = list(file_names)
    num_signals_processed = 0
    for file_name in file_names:
        signals_metadata = pd.read_parquet(file_name)
        signals_metadata = signals_metadata.rename(
            columns=dict(shot_nums="shot_id")
        )
        if len(signals_metadata) == 0 or "shot_id" not in signals_metadata.columns:
            continue
        df = signals_metadata
        df = df[df.shot_id <= LAST_MAST_SHOT].copy()
        df = df.rename({"dataset_item_uuid": "uuid"}, axis=1)
        df["uuid"] = [
            get_dataset_item_uuid(item["name"], item["shot_id"])
            for key, item in df.iterrows()
        ]
        df["quality"] = df["status"].map(lookup_status_code)
        df["shape"] = df["shape"].map(
            lambda x: x.tolist() if x is not None else None
        )
        df["url"] = (
            "s3://mast/shots/M9/" + df["shot_id"].map(str) + ".zarr/" + df["group"]
        )
        df["version"] = 0
        df["signal_type"] = df["type"]
        if "IMAGE_SUBCLASS" not in df:
            df["IMAGE_SUBCLASS"] = None
        df["subclass"] = df["IMAGE_SUBCLASS"]
        if "format" not in df:
            df["format"] = None
        if "units" not in df:
            df['units'] = ''
        columns = [
            "uuid",
            "shot_id",
            "quality",
            "shape",
            "name",
            "url",
            "version",
            "units",
            "signal_type",
            "description",
            "subclass",
            "format",
        ]
        df = df[columns]
        df = df.set_index("shot_id")
        df.to_sql("signals", url, if_exists="append")
        num_signals_processed = num_signals_processed + 1
        if num_signals_processed >= num_signals:
            break


def create_sources(url, data_path: Path):
    source_metadata = pd.read_parquet(data_path.parent / "sources_metadata.parquet")
    source_metadata["name"] = source_metadata["source_alias"]
    source_metadata["source_type"] = source_metadata["type"]
    source_metadata = source_metadata[["description", "name", "source_type"]]
    source_metadata = source_metadata.drop_duplicates()
    source_metadata = source_metadata.sort_values("name")
    source_metadata.to_sql("sources", url, if_exists="append", index=False)

