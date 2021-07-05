import graphene
from django.contrib.auth import login, logout

from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType
from utils.graphene.mutation import generate_input_type_for_serializer

from .serializers import LoginSerializer
from .schema import MeUserType


LoginInputType = generate_input_type_for_serializer(
    'LoginInputType',
    LoginSerializer
)


class Login(graphene.Mutation):
    class Arguments:
        data = LoginInputType(required=True)

    result = graphene.Field(MeUserType)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)
    captcha_required = graphene.Boolean(required=True, default_value=False)

    @staticmethod
    def mutate(root, info, data):
        serializer = LoginSerializer(data=data, context={'request': info.context.request})
        errors = mutation_is_not_valid(serializer)
        if errors:
            is_captcha_required = LoginSerializer.is_captcha_required(email=data['email'])
            return Login(
                errors=errors,
                ok=False,
                captcha_required=is_captcha_required,
            )
        if user := serializer.validated_data.get('user'):
            login(info.context.request, user)
        return Login(
            result=user,
            errors=None,
            ok=True
        )


class Logout(graphene.Mutation):
    ok = graphene.Boolean()

    def mutate(self, info, *args, **kwargs):
        if info.context.user.is_authenticated:
            logout(info.context.request)
        return Logout(ok=True)


class Mutation():
    login = Login.Field()
    logout = Logout.Field()
