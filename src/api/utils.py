import typing as t
from pydantic import create_model


def is_optional(type_):
    """Check if a type is optional. For example t.Optional[int] is optional,"""
    return t.get_origin(type_) is t.Union and type(None) in t.get_args(type_)


def is_list(type_):
    """Check if a type is a List. For example t.List[int]"""
    return t.get_origin(type_) is list


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


def InputParams(type_):
    """Return an input type for JSON API with all parameters

    This will create a type corresponding with the same properties
    as the SQL model as an input type to the API.
    """
    type_name = type_.__name__
    type_hints = t.get_type_hints(type_)
    fields = {}
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            fields[name] = (unwrap_optional(field_type), None)

    return create_model(f"{type_name}Params", **fields)


def create_model_column_metadata(model_cls):
    type_hints = t.get_type_hints(model_cls)
    metadata = {}
    for name, field_type in type_hints.items():
        if not name.startswith("__") and name != "metadata":
            if is_optional(field_type):
                metadata[name] = "object"
            elif field_type in (str, bool, int, float):
                metadata[name] = field_type.__name__
            else:
                metadata[name] = "object"
    return metadata
