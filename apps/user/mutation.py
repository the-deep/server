import graphene
from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType
from utils.graphene.mutation import generate_input_type_for_serializer

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    GqPasswordResetSerializer as ResetPasswordSerializer,
    PasswordChangeSerializer,
    UserMeSerializer,
    HIDLoginSerializer,
    UserDeleteSerializer,
)
from .schema import UserMeType


LoginInputType = generate_input_type_for_serializer('LoginInputType', LoginSerializer)
HIDLoginInputType = generate_input_type_for_serializer('HIDLoginInputType', HIDLoginSerializer)
RegisterInputType = generate_input_type_for_serializer('RegisterInputType', RegisterSerializer)
ResetPasswordInputType = generate_input_type_for_serializer('ResetPasswordInputType', ResetPasswordSerializer)
PasswordChangeInputType = generate_input_type_for_serializer('PasswordChangeInputType', PasswordChangeSerializer)
UserMeInputType = generate_input_type_for_serializer('UserMeInputType', UserMeSerializer)
UserDeleteInputType = generate_input_type_for_serializer(
    'UserDeleteInputType',
    UserDeleteSerializer
)


class Login(graphene.Mutation):
    class Arguments:
        data = LoginInputType(required=True)

    result = graphene.Field(UserMeType)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)
    captcha_required = graphene.Boolean(required=True, default_value=False)

    @staticmethod
    def mutate(root, info, data):
        serializer = LoginSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return Login(
                errors=errors,
                ok=False,
                captcha_required=LoginSerializer.is_captcha_required(email=data['email']),
            )
        if user := serializer.validated_data.get('user'):
            login(info.context.request, user)
        return Login(
            result=user,
            errors=None,
            ok=True
        )


class LoginWithHID(graphene.Mutation):
    class Arguments:
        data = HIDLoginInputType(required=True)

    result = graphene.Field(UserMeType)
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)

    @staticmethod
    def mutate(root, info, data):
        serializer = HIDLoginSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return LoginWithHID(errors=errors, ok=False)
        if user := serializer.validated_data.get('user'):
            login(info.context.request, user)
        return LoginWithHID(
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


class Register(graphene.Mutation):
    class Arguments:
        data = RegisterInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)
    captcha_required = graphene.Boolean(required=True, default_value=True)  # Always True in Register

    @staticmethod
    def mutate(root, info, data):
        serializer = RegisterSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return Register(
                errors=errors,
                ok=False,
            )
        serializer.save()
        return Register(
            errors=None,
            ok=True
        )


class ResetPassword(graphene.Mutation):
    class Arguments:
        data = ResetPasswordInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean(required=True)
    captcha_required = graphene.Boolean(required=True, default_value=True)  # Always True in ResetPassword

    @staticmethod
    def mutate(root, info, data):
        serializer = ResetPasswordSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return ResetPassword(
                errors=errors,
                ok=False,
            )
        serializer.save()
        return ResetPassword(
            errors=None,
            ok=True
        )


class ChangeUserPassword(graphene.Mutation):
    class Arguments:
        data = PasswordChangeInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()

    @staticmethod
    def mutate(root, info, data):
        serializer = PasswordChangeSerializer(data=data, context={'request': info.context.request})
        if errors := mutation_is_not_valid(serializer):
            return ChangeUserPassword(errors=errors, ok=False)
        serializer.save()
        update_session_auth_hash(info.context.request, info.context.request.user)
        return ChangeUserPassword(errors=None, ok=True)


class UpdateMe(graphene.Mutation):
    class Arguments:
        data = UserMeInputType(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserMeType)

    @staticmethod
    def mutate(root, info, data):
        serializer = UserMeSerializer(
            instance=info.context.user,
            data=data,
            context={'request': info.context.request},
        )
        if errors := mutation_is_not_valid(serializer):
            return UpdateMe(errors=errors, ok=False)
        serializer.save()
        return UpdateMe(result=serializer.instance, errors=None, ok=True)


class UserDelete(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserMeType)

    @staticmethod
    def mutate(root, info, id):
        user = User.objects.get(id=id)
        from project.models import ProjectMembership, ProjectRole

        if ProjectMembership.objects.filter(
            member=id,
            role__type=ProjectRole.Type.ADMIN
        ).exists():
            return UserDelete(
                errors=[
                    dict(
                        field='nonFieldErrors',
                        messages='You are admin in Projects.Choose another Project admin before you delete yourself',
                    )
                ], ok=False
            )

        user.profile.old_display_name = user.username
        user.first_name = settings.DELETED_USER_FIRST_NAME
        user.last_name = settings.DELETED_USER_LAST_NAME
        user.profile.deleted_at = timezone.now().date()
        user.save()
        return UserDelete(result=user, errors=None, ok=True)


class Mutation():
    login = Login.Field()
    login_with_hid = LoginWithHID.Field()
    logout = Logout.Field()
    register = Register.Field()
    reset_password = ResetPassword.Field()
    change_password = ChangeUserPassword.Field()
    update_me = UpdateMe.Field()
    delete_user = UserDelete.Field()
