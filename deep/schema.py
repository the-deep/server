import graphene
from graphene_django.debug import DjangoDebug
from django.conf import settings

# Importing for initialization (Make sure to import this before apps.<>)
"""
FYI, NOTE
Make sure use string import outside graphene files.
For eg: In filters.py use 'entry.schema.EntryListType' instead of `from entry.schema import EntryListType'
"""
from .graphene_converter import *  # type: ignore # noqa F401
from utils.graphene.resolver import *  # type: ignore # noqa F401

from project import schema as pj_schema, mutation as pj_mutation
from lead import public_schema as lead_public_schema
from analysis_framework import mutation as af_mutation, schema as af_schema
from user import mutation as user_mutation, schema as user_schema
from user_group import mutation as user_group_mutation, schema as user_group_schema
from organization import schema as organization_schema
from geo import schema as geo_schema
from notification import schema as notification_schema, mutation as notification_mutation
from assisted_tagging import schema as assisted_tagging_schema


class Query(
    pj_schema.Query,
    af_schema.Query,
    user_schema.Query,
    user_group_schema.Query,
    organization_schema.Query,
    geo_schema.Query,
    notification_schema.Query,
    lead_public_schema.Query,
    graphene.ObjectType
):
    assisted_tagging = graphene.Field(assisted_tagging_schema.AssistedTaggingRootQueryType)

    if settings.DEBUG:
        _debug = graphene.Field(DjangoDebug, name="_debug")

    @staticmethod
    def resolve_assisted_tagging(root, info, **kwargs):
        return {}


class Mutation(
    af_mutation.Mutation,
    user_mutation.Mutation,
    user_group_mutation.Mutation,
    pj_mutation.Mutation,
    notification_mutation.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
