from graphene import String
from graphene_django_extras.paginations.pagination import BaseDjangoGraphqlPagination


class OrderingOnlyArgumentPagination(BaseDjangoGraphqlPagination):
    """
    Pagination just for ordering. Created for DjangoFilterPaginateListField (or its subclasses) in mind, to remove the
    page related arguments.
    """
    __name__ = "OrderingOnlyArgument"

    def __init__(
        self,
        ordering="",
        ordering_param="ordering",
    ):
        # Default ordering value: ""
        self.ordering = ordering

        # A string or comma delimited string values that indicate the default ordering when obtaining lists of objects.
        # Uses Django order_by syntax
        self.ordering_param = ordering_param

    def to_dict(self):
        return {
            "ordering_param": self.ordering_param,
            "ordering": self.ordering,
        }

    def to_graphql_fields(self):
        argument_dict = {
            self.ordering_param: String(
                description="A string or comma delimited string values that indicate the "
                "default ordering when obtaining lists of objects."
            ),
        }

        return argument_dict

    def paginate_queryset(self, qs, **kwargs):
        order = kwargs.pop(self.ordering_param, None) or self.ordering
        if order:
            if "," in order:
                order = order.strip(",").replace(" ", "").split(",")
                if order.__len__() > 0:
                    qs = qs.order_by(*order)
            else:
                qs = qs.order_by(order)

        return qs
