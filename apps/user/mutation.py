import graphene
from django.contrib.auth import login, logout
from django.contrib.auth import update_session_auth_hash
from django.db import models

from utils.graphene.error_types import mutation_is_not_valid, CustomErrorType
from utils.graphene.mutation import generate_input_type_for_serializer

from .serializers import (
    LoginSerializer,
    RegisterSerializer,
    GqPasswordResetSerializer as ResetPasswordSerializer,
    PasswordChangeSerializer,
    UserMeSerializer,
    HIDLoginSerializer,
)
from .schema import UserMeType


LoginInputType = generate_input_type_for_serializer('LoginInputType', LoginSerializer)
HIDLoginInputType = generate_input_type_for_serializer('HIDLoginInputType', HIDLoginSerializer)
RegisterInputType = generate_input_type_for_serializer('RegisterInputType', RegisterSerializer)
ResetPasswordInputType = generate_input_type_for_serializer('ResetPasswordInputType', ResetPasswordSerializer)
PasswordChangeInputType = generate_input_type_for_serializer('PasswordChangeInputType', PasswordChangeSerializer)
UserMeInputType = generate_input_type_for_serializer('UserMeInputType', UserMeSerializer)


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
    errors = graphene.List(graphene.NonNull(CustomErrorType))
    ok = graphene.Boolean()
    result = graphene.Field(UserMeType)

    @staticmethod
    def mutate(_, info):
        from project.models import ProjectMembership, ProjectRole

        current_user = info.context.user
        if current_user.profile.deleted_at:
            return UserDelete(
                errors=[
                    dict(
                        field='nonFieldErrors',
                        messages='Already deleted.'
                    )
                ]
            )

        def user_member_project_ids(owner=False):
            # Member in Projects
            project_ids = ProjectMembership.objects.filter(member=current_user).values('project')
            extra_filter = {}
            if owner:
                project_ids = project_ids.filter(role__type=ProjectRole.Type.PROJECT_OWNER)
                extra_filter['role__type'] = ProjectRole.Type.PROJECT_OWNER
            return ProjectMembership.objects.filter(
                member__profile__deleted_at__isnull=True,  # Exclude already deleted users
                project__in=project_ids,
                **extra_filter,
            ).order_by().values('project').annotate(
                member_count=models.Count('member', distinct=True),
            ).filter(member_count=1).values_list('project', 'project__title')

        only_user_member_projects = user_member_project_ids()
        if only_user_member_projects:
            return UserDelete(
                errors=[
                    dict(
                        field='nonFieldErrors',
                        messages='You are only the member in Projects %s. Choose other members before you delete yourself.'
                        % ', '.join([f'[{_id}]{title}' for _id, title in only_user_member_projects]),
                    )
                ], ok=False
            )

        # user only the owner in the project
        only_user_owner_role_in_projects = user_member_project_ids(owner=True)
        if only_user_owner_role_in_projects:
            return UserDelete(
                errors=[
                    dict(
                        field='nonFieldErrors',
                        messages='You are Owner in Projects %s. Choose another Project Owner before you delete yourself.'
                        % ', '.join([f'[{_id}]{title}' for _id, title in only_user_owner_role_in_projects]),
                    )
                ], ok=False
            )
        current_user.soft_delete()
        return UserDelete(result=current_user, errors=None, ok=True)


class Mutation():
    login = Login.Field()
    login_with_hid = LoginWithHID.Field()
    logout = Logout.Field()
    register = Register.Field()
    reset_password = ResetPassword.Field()
    change_password = ChangeUserPassword.Field()
    update_me = UpdateMe.Field()
    delete_user = UserDelete.Field()
