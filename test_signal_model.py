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
from data_creation_for_test import create_cpf_summary, create_scenarios, create_shots, create_signals, create_sources, create_shot_source_links

data_path = "/Users/pstanis/Documents/work_projects/fair-mast/data/metadata/prod"
data_path = Path(data_path)

# create the test database
host = os.environ.get("DATABASE_HOST", "localhost")
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"
LAST_MAST_SHOT = 30471

if database_exists(SQLALCHEMY_DATABASE_TEST_URL):
    drop_database(SQLALCHEMY_DATABASE_TEST_URL)
create_database(SQLALCHEMY_DATABASE_TEST_URL)

engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# need this to make sure we don't use the other app when using the API
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()
app.dependency_overrides[get_db] = override_get_db


# ========= Tests ==========

@pytest.fixture(scope="module")
def client():
    client = TestClient(app)
    return client


# this is needed for the create_all_part, so keep test_source_valid or need to figure this bit out again
@pytest.fixture(scope="module")
def db_session():
    SQLModel.metadata.create_all(engine)
    session = TestingSessionLocal()
    yield session
    session.rollback()
    session.close()

def test_source_valid(db_session):
    valid_source = SourceModel(
        doi=None,
        name="test",
        description="test",
        source_type="Analysed"
        )
    db_session.add(valid_source)
    db_session.commit()
    sample_article = db_session.query(SourceModel).first()
    item = sample_article.dict(exclude_none=True)
    assert sample_article.name == "test"
    assert len(item) == 3

def test_get_cpf(client):
    create_cpf_summary(SQLALCHEMY_DATABASE_TEST_URL, data_path)
    response = client.get("json/cpf_summary")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 265

def test_get_scenarios(client):
    create_scenarios(SQLALCHEMY_DATABASE_TEST_URL, data_path)
    response = client.get("json/scenarios")
    data = response.json()
    assert response.status_code == 200
    
def test_get_shots(client):
    create_shots(SQLALCHEMY_DATABASE_TEST_URL, data_path)
    response = client.get("json/shots")
    data = response.json()
    assert response.status_code == 200

# will only be signals for shot 25877, can change number of shots in data_creation_for_test.py
def test_get_signals(client):
    create_signals(SQLALCHEMY_DATABASE_TEST_URL, data_path, num_signals=1)
    response = client.get("json/signals")
    data = response.json()
    assert response.status_code == 200
    assert data[0]['shot_id'] == 25877

def test_get_sources(client):
    create_sources(SQLALCHEMY_DATABASE_TEST_URL, data_path)
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    print(data)