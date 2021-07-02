import graphene

from analysis_framework import mutation as af_mutations, schema as af_schema


class Query(
    af_schema.Query,
    graphene.ObjectType
):
    pass


class Mutation(
    af_mutations.Mutation,
    graphene.ObjectType
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
