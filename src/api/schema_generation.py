import collections
import dataclasses
import enum
import typing as t
from enum import Enum
from types import SimpleNamespace

import strawberry
from strawberry.type import StrawberryContainer
from .query_generation import create_all_type_resolver


class BoolOps(SimpleNamespace):
    eq = "eq"
    neq = "neq"
    lt = "lt"
    lte = "lte"
    gt = "gt"
    gte = "gte"

    contains = "contains"
    not_contains = "not_contains"

    in_ = "in_"
    not_in = "not_in"

    is_null_ = "is_null"


_BOOL_OP_COMPARISONS = {
    BoolOps.eq,
    BoolOps.neq,
    BoolOps.lt,
    BoolOps.lte,
    BoolOps.gt,
    BoolOps.gte,
}

_SAME_TYPE_BOOL_OP = _BOOL_OP_COMPARISONS
_INCLUSION_BOOL_OP = {BoolOps.in_, BoolOps.not_in}
_CONTAINS_BOOL_OP = {BoolOps.contains, BoolOps.not_contains}

_SCALAR_BOOL_OP_MAP: dict[type, set[str]] = {
    bool: {BoolOps.eq, BoolOps.neq},
    int: {*_BOOL_OP_COMPARISONS, *_INCLUSION_BOOL_OP},
    float: {*_BOOL_OP_COMPARISONS, *_INCLUSION_BOOL_OP},
    str: {*_BOOL_OP_COMPARISONS, *_INCLUSION_BOOL_OP, *_CONTAINS_BOOL_OP},
    set: {*_CONTAINS_BOOL_OP},
    list: {*_CONTAINS_BOOL_OP},
}


@strawberry.enum
class OrderByEnum(Enum):
    asc = "asc"
    asc_nulls_first = "asc_nulls_first"
    asc_nulls_last = "asc_nulls_last"
    desc = "desc"
    desc_nulls_first = "desc_nulls_first"
    desc_nulls_last = "desc_nulls_last"


PRIMITIVES = {int, str, bool, float}


def is_sequence_container(type_):
    """Check if a type is a container. For example t.List[int] is a container,"""
    # TODO: this is hacky. see is_primitive for why we have it
    origin = t.get_origin(type_)
    return origin is t.List or origin is t.Set


def is_optional(type_):
    """Check if a type is optional. For example t.Optional[int] is optional,"""
    return t.get_origin(type_) is t.Union and type(None) in t.get_args(type_)


def unwrap_sequence_container(type_):
    """Return the inside of a container. For example t.List[int]
    would return int.
    """
    # TODO: this is hacky. see is_primitive for why we have it
    if is_sequence_container(type_):
        if len(t.get_args(type_)) > 1:
            raise ValueError(
                "Unable to unwrap fields which may contain multiple types "
                + f"of scalars: {type_}"
            )
        return t.get_args(type_)[0]
    return type_


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


def is_primitive(type_):
    # TODO: this is hacky. We want to understand if types are primitive or not
    # but really we just want to know if they are handled by sql as a column
    # or as a relationship
    # int is a column
    # list[int] could be a column (we can assume it is)
    # list[address] is a relationship
    while is_optional(type_) or is_sequence_container(type_):
        type_ = unwrap_optional(type_)
        type_ = unwrap_sequence_container(type_)
    return isinstance(type_, collections.abc.Hashable) and type_ in PRIMITIVES


def create_comparison_expression_name(type_):
    # TODO: this is a hack we rely on the fact that users probably won't pass
    # lazy types which are wrapped
    if isinstance(type_, strawberry.LazyType):
        return f"{type_.type_name}Filter"
    generics = t.get_args(type_)
    return (
        "".join(g.__name__.capitalize() for g in generics)
        + type_.__name__.capitalize()
        + "Filter"
    )


def create_order_by_expression_name(type_):
    generics = t.get_args(type_)
    return (
        "".join(g.__name__.capitalize() for g in generics)
        + type_.__name__.capitalize()
        + "OrderBy"
    )


def create_all_type_query_name(type_):
    type_name = type_.__name__.capitalize()
    if not type_name.endswith("s"):
        type_name += "s"
    return f"all_{type_name}"


def create_select_column_enum_name(type_):
    type_name = type_.__name__.capitalize()
    if not type_name.endswith("s"):
        type_name += "s"
    return f"{type_name}SelectColumn"


class ComparisonExpression:
    pass


class ScalarComparison(ComparisonExpression):
    pass


class NonScalarComparison(ComparisonExpression):
    pass


def create_scalar_comparison_expression(type_: type):
    type_ = unwrap_optional(type_)
    operations = _SCALAR_BOOL_OP_MAP[t.get_origin(type_) or type_]
    fields = []
    for op in operations:
        if op in _SAME_TYPE_BOOL_OP:
            fields.append((op, t.Optional[type_], dataclasses.field(default=None)))

        elif op in _INCLUSION_BOOL_OP:
            fields.append(
                (op, t.Optional[t.List[type_]], dataclasses.field(default=None))
            )

        elif op in _CONTAINS_BOOL_OP:
            generic_args = t.get_args(type_)
            container_type = t.get_origin(type_) or type_

            if len(generic_args) == 1:
                resulting_type = t.Optional[container_type[generic_args[0]]]
            else:
                resulting_type = t.Optional[container_type]

            fields.append((op, resulting_type, dataclasses.field(default=None)))

    # TODO: would be nice to only add is_null if the field is optional.
    # but we would need to change the `expression_name` since we register
    # the expression as a global and whichever class we define last will
    # override prior classes
    fields.append((BoolOps.is_null_, t.Optional[bool], dataclasses.field(default=None)))

    expression_name = create_comparison_expression_name(type_)
    globals()[expression_name] = dataclasses.make_dataclass(
        expression_name,
        fields=fields,
        namespace={"__module__": __name__},
        bases=(ScalarComparison,),
    )
    return strawberry.input(globals()[expression_name])


def create_non_scalar_comparison_expression(type_: type):
    type_hints = t.get_type_hints(type_)
    fields = []
    expression_name = create_comparison_expression_name(type_)
    for field_name, field_type in type_hints.items():
        if is_primitive(field_type):
            fields.append(
                (
                    field_name,
                    t.Optional[create_scalar_comparison_expression(field_type)],
                    dataclasses.field(default=None),
                )
            )
        else:
            # the base type is the underlying type of the field.
            # we don't care if the field is optional or a list we just want
            # to implement a filter for the underlying type
            # TODO: not sure if StrawberryContainer is always the right choice
            field_base_type = field_type
            if isinstance(field_type, StrawberryContainer):
                field_base_type = field_type.of_type

            if isinstance(field_base_type, strawberry.LazyType):
                fields.append(
                    (
                        field_name,
                        t.Optional[
                            strawberry.LazyType[
                                # TODO: this is a hack. We cannot resolve the
                                # type of the nested field or we get a circular
                                # dependency error. Instead we rely on the fact
                                # that the type underlying the LazyType will
                                # be used in a non lazy way elsewhere and
                                # registed on the module associated with __name__
                                create_comparison_expression_name(field_type),
                                __name__,
                            ]
                        ],
                        dataclasses.field(default=None),
                    )
                )

            else:
                # this code handles the case where the field is a single item
                fields.append(
                    (
                        field_name,
                        t.Optional[
                            create_non_scalar_comparison_expression(field_base_type)
                        ],
                        dataclasses.field(default=None),
                    )
                )

    fields.append(
        ("and_", t.Optional[t.List[expression_name]], dataclasses.field(default=None)),
    )
    fields.append(
        ("or_", t.Optional[t.List[expression_name]], dataclasses.field(default=None)),
    )
    globals()[expression_name] = dataclasses.make_dataclass(
        expression_name,
        fields=fields,
        namespace={"__module__": __name__},
        bases=(NonScalarComparison,),
    )
    return strawberry.input(globals()[expression_name])


def create_non_scalar_order_by_expression(type_: type):
    type_hints = t.get_type_hints(type_)
    fields = []
    expression_name = create_order_by_expression_name(type_)
    for field_name, field_type in type_hints.items():
        fields.append(
            (
                field_name,
                t.Optional[OrderByEnum],
                dataclasses.field(default=None),
            )
        )
    globals()[expression_name] = dataclasses.make_dataclass(
        expression_name,
        fields=fields,
        namespace={"__module__": __name__},
    )
    return strawberry.input(globals()[expression_name])


def create_non_scalar_select_columns_enum(type_: type):
    enum_name = create_select_column_enum_name(type_)
    type_hints = t.get_type_hints(type_)

    globals()[enum_name] = enum.Enum(
        enum_name, {field_name: field_name for field_name in type_hints.keys()}
    )
    return strawberry.enum(globals()[enum_name])


def create_array_relationship_resolver(type_: type):
    return create_all_type_resolver(type_)


def create_all_type_query_field(type_: type):
    method_name = create_all_type_query_name(type_)

    all_type_query_implementation = create_array_relationship_resolver(type_)

    return (
        method_name,
        t.List[type_],
        dataclasses.field(default=strawberry.field(all_type_query_implementation)),
    )


def create_generation_context(types: t.List[type]):
    type_to_model = {type_: type_._pydantic_type for type_ in types}
    model_to_type = {type_._pydantic_type: type_ for type_ in types}
    type_to_type_definition = {type_: type_._type_definition for type_ in types}
    type_definition_to_type = {type_._type_definition: type_ for type_ in types}
    type_to_mapper = {type_: type_._pydantic_type.__mapper__ for type_ in types}
    mapper_to_type = {type_._pydantic_type.__mapper__: type_ for type_ in types}
    context = {
        "type_to_model": type_to_model,
        "model_to_type": model_to_type,
        "type_to_type_definition": type_to_type_definition,
        "type_definition_to_type": type_definition_to_type,
        "type_to_mapper": type_to_mapper,
        "mapper_to_type": mapper_to_type,
    }
    return context


def create_query_root(types: t.List[type]):
    create_generation_context(types)

    all_type_queries = [create_all_type_query_field(type_) for type_ in types]

    query_root_name = "query_root"
    globals()[query_root_name] = dataclasses.make_dataclass(
        query_root_name,
        fields=[*all_type_queries],
        namespace={
            **{"__module__": __name__},
        },
    )

    return strawberry.type(globals()[query_root_name])
