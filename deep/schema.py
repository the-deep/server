import graphene
from graphene_django.debug import DjangoDebug
from django.conf import settings

from project import schema as pj_schema
from analysis_framework import mutation as af_mutation, schema as af_schema
from user import mutation as user_mutation, schema as user_schema
from user_group import mutation as user_group_mutation, schema as user_group_schema


class Query(
    pj_schema.Query,
    af_schema.Query,
    user_schema.Query,
    user_group_schema.Query,
    graphene.ObjectType
):
    if settings.DEBUG:
        _debug = graphene.Field(DjangoDebug, name="_debug")


class Mutation(
    af_mutation.Mutation,
    user_mutation.Mutation,
    user_group_mutation.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
