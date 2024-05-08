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
from src.api.create import DBCreationClient
from pathlib import Path
from sqlalchemy_utils.functions import (
    drop_database,
    database_exists,
    create_database,
)

# create the test database
host = os.environ.get("DATABASE_HOST", "localhost")
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"

if database_exists(SQLALCHEMY_DATABASE_TEST_URL):
    drop_database(SQLALCHEMY_DATABASE_TEST_URL)
    create_database(SQLALCHEMY_DATABASE_TEST_URL)
else:
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
        name="acd",
        description="Carbon density",
        source_type="Analysed"
        )
    db_session.add(valid_source)
    db_session.commit()
    sample_article = db_session.query(SourceModel).first()
    item = sample_article.dict(exclude_none=True)
    assert sample_article.name == "acd"
    assert len(item) == 3

def test_get_sources(client):
    response = client.get("json/sources")
    data = response.json()
    assert response.status_code == 200
    print(data)