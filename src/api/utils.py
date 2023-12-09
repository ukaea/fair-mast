import typing as t
import sqlmodel
from sqlalchemy import func
from sqlalchemy.sql.operators import is_, is_not
from sqlmodel.main import SQLModel
from pydantic import create_model


def is_optional(type_):
    """Check if a type is optional. For example t.Optional[int] is optional,"""
    return t.get_origin(type_) is t.Union and type(None) in t.get_args(type_)


def is_list(type_):
    """Check if a type is a List. For example t.List[int]"""
    return t.get_origin(type_) is list


def unwrap_type(type_):
    if len(t.get_args(type_)) == 0:
        return type_
    return [t_ for t_ in t.get_args(type_) if t_ is not None][0]


def unwrap_optional(type_):
    """Return the non optional version of a type. For example t.Optional[int]
    would return int.
    """
    if is_optional(type_):
        if len(t.get_args(type_)) > 2:
            raise ValueError(
                "Unable to unwrap fields which may contain multiple types "
                + f"of scalars: {type_}"
            )
        return [t_ for t_ in t.get_args(type_) if t_ is not None][0]
    return type_


def get_fields(type_):
    type_hints = t.get_type_hints(type_)
    fields = {}
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            fields[name] = (unwrap_optional(field_type), None)
    return fields


def get_fields_non_optional(type_):
    type_hints = t.get_type_hints(type_)
    fields = {}
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            if not is_optional(field_type):
                fields[name] = (unwrap_optional(field_type), None)
    return fields


def InputParams(type_):
    """Return an input type for JSON API with all parameters

    This will create a type corresponding with the same properties
    as the SQL model as an input type to the API.
    """
    type_name = type_.__name__
    fields = get_fields(type_)
    return create_model(f"{type_name}Params", **fields)


def create_model_column_metadata(model_cls):
    type_hints = t.get_type_hints(model_cls)
    metadata = {}
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            if is_list(field_type) and SQLModel in unwrap_type(field_type).__bases__:
                continue

            if is_optional(field_type):
                metadata[name] = "object"
            elif field_type in (str, bool, int, float):
                metadata[name] = field_type.__name__
            else:
                metadata[name] = "object"
    return metadata


comparator_map = {
    "contains": lambda column, value: column.contains(value),
    "isNull": lambda column, value: (is_(column, None)),  # XOR
    "isNotNull": lambda column, value: (is_not(column, None)),  # XOR
    "eq": lambda column, value: column == value,
    "neq": lambda column, value: column != value,
    "lt": lambda column, value: column < value,
    "gt": lambda column, value: column > value,
    "lte": lambda column, value: column <= value,
    "gte": lambda column, value: column >= value,
}

aggregate_map = {
    "mean": func.avg,
    "sum": func.sum,
    "max": func.max,
    "min": func.min,
    "distinct": func.distinct,
    "count": func.count,
}
