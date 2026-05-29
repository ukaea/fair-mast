import datetime
import os
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import (
    drop_database,
)
from sqlmodel import Session, create_engine
from strawberry.extensions import SchemaExtension

from src.api.create import create_db_and_tables
from src.api.database import get_db
from src.api.main import app, graphql_app
from src.api.models import Level2ShotModel, ShotModel, SourceModel
from src.api.types import (
    Commissioner,
    CurrentRange,
    DivertorConfig,
    Facility,
    PlasmaShape,
    Quality,
)

# Set up the database URL
host = os.environ.get("DATABASE_HOST", "localhost")
TEST_DB_NAME = "test_db"
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/{TEST_DB_NAME}"


# Fixture to create and drop the database
@pytest.fixture(scope="session")
def test_db(data_path):
    data_path = Path(data_path)
    create_db_and_tables(str(data_path), SQLALCHEMY_DATABASE_TEST_URL, TEST_DB_NAME)
    engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL, echo=True)

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


# Synthetic ShotModel/SourceModel factories for unit tests that don't need a
# DB. `# type: ignore[call-arg]` suppresses pyright complaints about the ~180
# Optional cpf_* fields on BaseShotModel which default to None at runtime but
# look required to a strict type checker.
SHOT_TIMESTAMP = datetime.datetime(2013, 8, 9, 14, 23, 11, tzinfo=datetime.timezone.utc)


def make_shot(cls: type[ShotModel] | type[Level2ShotModel] = ShotModel):
    return cls(  # type: ignore[call-arg]
        shot_id=30420,
        uuid=uuid.UUID("e6c5f29a-9b2a-5e54-9b32-7e8f1c0e1b1f"),
        url="s3://mast/level1/shots/30420.zarr",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        timestamp=SHOT_TIMESTAMP,
        preshot_description="L-mode reference shot.",
        postshot_description="Stable plasma.",
        campaign="M9",
        facility=Facility.mast,
        divertor_config=DivertorConfig.conventional,
        plasma_shape=PlasmaShape.connected_double_null,
        current_range=CurrentRange._700kA,
        commissioner=Commissioner.ukaea,
        heating="NBI",
        type_="dcat:Dataset",
        title="Shot Dataset",
        context_={},
    )


def make_source(name="AMC", description=None):
    return SourceModel(  # type: ignore[call-arg]
        shot_id=30420,
        name=name,
        title="Source Dataset",  # boilerplate server_default — should NOT be used as display name
        description=description or f"{name} diagnostic.",
        url=f"s3://mast/level1/shots/30420.zarr/{name}",
        endpoint_url="https://s3.echo.stfc.ac.uk",
        uuid=uuid.uuid5(uuid.NAMESPACE_OID, name),
        quality=Quality.validated,
        type_="dcat:Dataset",
        context_={},
    )


@pytest.fixture
def shot():
    return make_shot()


@pytest.fixture
def sources():
    return [
        make_source("AMC", "Plasma current and magnetic equilibrium signals."),
        make_source("AYC", "Electron temperature and density."),
    ]
