import typing as t

import strawberry
from sqlmodel import Session
from strawberry.extensions import Extension

from .schema_generation import (
    create_array_relationship_resolver,
    create_generation_context,
    create_query_root,
)
from .database import engine
from .models import ShotModel


class SQLAlchemySession(Extension):
    def on_request_start(self):
        self.execution_context.context["db"] = Session(
            autocommit=False, autoflush=False, bind=engine, future=True
        )

    def on_request_end(self):
        self.execution_context.context["db"].close()


@strawberry.experimental.pydantic.type(model=ShotModel, fields=["shot_id"])
class Shot:
    pass


auto_types = [Shot]
auto_schema_context = create_generation_context(auto_types)


class AutoSchemaContext(Extension):
    def on_request_start(self):
        self.execution_context.context["auto_schema"] = auto_schema_context


Query = create_query_root(auto_types)

schema = strawberry.Schema(
    query=Query, extensions=[SQLAlchemySession, AutoSchemaContext]
)
