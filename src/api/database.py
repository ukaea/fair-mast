from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .environment import (
    SQLALCHEMY_DATABASE_URL,
    SQLALCHEMY_DEBUG,
)

engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=SQLALCHEMY_DEBUG)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
print(SQLALCHEMY_DATABASE_URL, "information")

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
