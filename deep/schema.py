import graphene


class Query(graphene.ObjectType):
    placeholder = graphene.String()


class Mutation(graphene.ObjectType):
    placeholder = graphene.String()


schema = graphene.Schema(query=Query, mutation=Mutation)
