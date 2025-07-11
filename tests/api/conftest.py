import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from requests.auth import HTTPBasicAuth
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import drop_database
from sqlmodel import Session, create_engine
from strawberry.extensions import SchemaExtension

from src.api.create import create_db_and_tables
from src.api.database import get_db
from src.api.environment import KEYCLOAK_PASSWORD, KEYCLOAK_USERNAME
from src.api.main import app, graphql_app

# Set up the database URL
host = os.environ.get("DATABASE_HOST", "localhost")
TEST_DB_NAME = "test_db"
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/{TEST_DB_NAME}"


# Fixture to create and drop the database
@pytest.fixture(scope="session")
def test_db(data_path):
    data_path = Path(data_path)
    create_db_and_tables(data_path, SQLALCHEMY_DATABASE_TEST_URL, TEST_DB_NAME)
    engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL, echo=True)

    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    yield TestingSessionLocal()

    drop_database(SQLALCHEMY_DATABASE_TEST_URL)


@pytest.fixture()
def test_auth():
    if not KEYCLOAK_USERNAME or not KEYCLOAK_PASSWORD:
        return None
    return HTTPBasicAuth(username=KEYCLOAK_USERNAME, password=KEYCLOAK_PASSWORD)


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
