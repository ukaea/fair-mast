import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
import os
from sqlmodel import Session, create_engine
from pathlib import Path
from sqlalchemy_utils.functions import (
    drop_database,
)
from strawberry.extensions import SchemaExtension
from src.api.create import DBCreationClient
from src.api.main import app, graphql_app
from src.api.database import get_db

# Fixture to get data path from command line
def pytest_addoption(parser):
    parser.addoption(
        "--data-path",
        action="store",
        default="~/data/metadata/mini",
        help="Path to mini data directory",
    )

@pytest.fixture(scope="session")
def data_path(request):
    return request.config.getoption("--data-path")

# Set up the database URL
host = os.environ.get("DATABASE_HOST", "localhost")
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"

# Fixture to create and drop the database
@pytest.fixture(scope="session")
def test_db(data_path):
    data_path = Path(data_path)
    client = DBCreationClient(SQLALCHEMY_DATABASE_TEST_URL)
    engine = client.create_database()
    client.create_cpf_summary(data_path)
    client.create_scenarios(data_path)
    client.create_shots(data_path)
    client.create_signals(data_path)
    client.create_sources(data_path)
    client.create_shot_source_links(data_path)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)        

    yield TestingSessionLocal()

    drop_database(SQLALCHEMY_DATABASE_TEST_URL)

class TestSQLAlchemySession(SchemaExtension):
    def on_request_start(self):
        engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL)
        self.execution_context.context["db"] = Session(
            autocommit=False, autoflush=False, bind=engine, future=True
        )

    def on_request_end(self):
        self.execution_context.context["db"].close()

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
    graphql_app.schema.extensions[0] = TestSQLAlchemySession

# Fixture to create a client for testing
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as client:
        yield client