import graphene

from analysis_framework import mutation as af_mutations, schema as af_schema
from user import mutation as user_mutations, schema as user_schema


class Query(
    af_schema.Query,
    user_schema.Query,
    graphene.ObjectType
):
    pass


class Mutation(
    af_mutations.Mutation,
    user_mutations.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
