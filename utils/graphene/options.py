from graphene.types.base import BaseOptions


class CustomObjectTypeOptions(BaseOptions):
    fields = None
    interfaces = ()
    base_type = None
    registry = None
    connection = None
    create_container = None
    results_field_name = None
    input_for = None
    filterset_class = None
