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
from data_creation_for_test import create_cpf_summary, create_scenarios, create_shots, create_signals, create_sources

data_path = "/Users/pstanis/Documents/work_projects/fair-mast/data/metadata/prod"

# Set up the database URL
host = os.environ.get("DATABASE_HOST", "localhost")
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"

# Fixture to create and drop the database
@pytest.fixture(scope="session")
def test_db():
    if database_exists(SQLALCHEMY_DATABASE_TEST_URL):
        drop_database(SQLALCHEMY_DATABASE_TEST_URL)
    create_database(SQLALCHEMY_DATABASE_TEST_URL)

    print("\n ---- Creating Test Database ----- \n")
    engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL)
    SQLModel.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    create_cpf_summary(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_scenarios(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_shots(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_signals(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path), num_signals=1)
    create_sources(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))

    yield TestingSessionLocal()

    print("\n ---- Testing Complete: Closing Database ----- \n")

    drop_database(SQLALCHEMY_DATABASE_TEST_URL)

    print("---- Database Closed -----")

# Fixture to override the database dependency
@pytest.fixture
def override_get_db(test_db):
    def override():
        try:
            db = test_db
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override

# Fixture to create a client for testing
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client

# ========= Tests ==========

def test_get_cpf(client, override_get_db):
    response = client.get("/json/cpf_summary")
    assert response.status_code == 200
    data = response.json()
    assert len(data['items']) == 50
    assert "description" in data['items'][0]

def test_get_scenarios(client, override_get_db):
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    
def test_get_shots(client, override_get_db):
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200

# will only be signals for shot 25877, can change number of shots in data_creation_for_test.py
def test_get_signals(client, override_get_db):
    response = client.get("json/signals")
    data = response.json()
    assert response.status_code == 200
    assert data[0]['shot_id'] == 25877

def test_get_sources(client, override_get_db):
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200

def test_get_shot_aggregate(client):
    response = client.get(
        "json/shots/aggregate?data=shot_id$min:,shot_id$max:&groupby=campaign&sort=-min_shot_id"
    )
    data = response.json()
    assert response.status_code == 200
    print(data)
    assert len(data) == 1
    assert data[0]["campaign"] == "M9"