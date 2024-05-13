import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from src.api.main import app
from src.api.database import get_db
import os
from sqlmodel import SQLModel, create_engine
from pathlib import Path
from sqlalchemy_utils.functions import (
    drop_database,
    database_exists,
    create_database,
)
from data_creation_for_test import create_cpf_summary, create_scenarios, create_shots, create_signals, create_sources, create_shot_source_links

# Set up the database URL
host = os.environ.get("DATABASE_HOST", "localhost")
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"

# Fixture to create and drop the database
@pytest.fixture(scope="session")
def test_db(data_path):
    if database_exists(SQLALCHEMY_DATABASE_TEST_URL):
        drop_database(SQLALCHEMY_DATABASE_TEST_URL)
    create_database(SQLALCHEMY_DATABASE_TEST_URL)

    print("\n ---- Creating Test Database ----- \n")
    engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL)
    SQLModel.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    print(data_path)

    create_cpf_summary(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_scenarios(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_shots(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_signals(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_sources(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))
    create_shot_source_links(SQLALCHEMY_DATABASE_TEST_URL, Path(data_path))

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
