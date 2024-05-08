import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.main import app
from src.api.database import get_db, Base
from src.api.models import SignalModel, SourceModel
import os
from sqlmodel import Field, Session, SQLModel, create_engine
from src.api.create import DBCreationClient

from sqlalchemy_utils.functions import (
    drop_database,
    database_exists,
    create_database,
)

host = os.environ.get("DATABASE_HOST", "localhost")
# Location of the database
SQLALCHEMY_DATABASE_TEST_URL = f"postgresql://root:root@{host}:5432/test_db"

if database_exists(SQLALCHEMY_DATABASE_TEST_URL):
    drop_database(SQLALCHEMY_DATABASE_TEST_URL)
    create_database(SQLALCHEMY_DATABASE_TEST_URL)
else:
    create_database(SQLALCHEMY_DATABASE_TEST_URL)

engine = create_engine(SQLALCHEMY_DATABASE_TEST_URL)
Session = sessionmaker(bind=engine)

# ========= Tests ==========

@pytest.fixture(scope="module")
def db_session():
    SQLModel.metadata.create_all(engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

class TestDB:
    def test_source_valid(self, db_session):
        valid_source = SourceModel(
            doi=None,
            name="acd",
            description="Carbon density",
            source_type="Analysed"
            )
        db_session.add(valid_source)
        db_session.commit()
        sample_article = db_session.query(SourceModel).first()
        assert sample_article.name == "acd"
    