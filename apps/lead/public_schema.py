import graphene
from django.db import models
from gallery.schema import PublicGalleryFileType
from project.public_schema import PublicProjectWithMembershipData

from deep.permissions import ProjectPermissions as PP
from utils.graphene.enums import EnumDescription

from .models import Lead
from .schema import LeadSourceTypeEnum


def get_public_lead_qs():
    return Lead.objects.filter(
        models.Q(
            project__has_publicly_viewable_unprotected_leads=True,
            confidentiality=Lead.Confidentiality.UNPROTECTED,
        )
        | models.Q(
            project__has_publicly_viewable_restricted_leads=True,
            confidentiality=Lead.Confidentiality.RESTRICTED,
        )
        | models.Q(
            project__has_publicly_viewable_confidential_leads=True,
            confidentiality=Lead.Confidentiality.CONFIDENTIAL,
        )
    )


class PublicLeadDetailType(graphene.ObjectType):
    uuid = graphene.UUID(required=True)
    project_title = graphene.String()
    created_by_display_name = graphene.String()
    source_title = graphene.String()
    source_url = graphene.String()
    published_on = graphene.Date()

    source_type = graphene.Field(LeadSourceTypeEnum, required=True)
    source_type_display = EnumDescription(source="get_source_type_display", required=True)
    text = graphene.String()
    url = graphene.String()
    attachment = graphene.Field(PublicGalleryFileType)
    title = graphene.String()

    @staticmethod
    def resolve_project_title(root, info, **_):
        if root.project.is_private and not root.has_project_access:
            return
        return root.project.title

    @staticmethod
    def resolve_created_by_display_name(root, info, **_):
        return root.created_by and root.created_by.get_display_name()

    @staticmethod
    def resolve_source_title(root, info, **_):
        return root.source and root.source.data.title

    @staticmethod
    def resolve_source_url(root, info, **_):
        return root.source and root.source.data.url


class PublicLeadMetaType(graphene.ObjectType):
    project = graphene.Field(PublicProjectWithMembershipData)
    lead = graphene.Field(PublicLeadDetailType)


class Query:
    public_lead = graphene.Field(
        PublicLeadMetaType,
        uuid=graphene.UUID(required=True),
    )

    @staticmethod
    def resolve_public_lead(_, info, **kwargs):
        def _return(lead, project, has_access):
            _project = project
            if (project and project.is_private) and not has_access:
                _project = None
            if lead:
                lead.has_project_access = has_access
            return {
                "project": _project,
                "lead": lead,
            }

        def _get_lead_from_qs(qs):
            return (
                qs.select_related(
                    "project",
                    "created_by",
                    "source",
                    "source__parent",
                )
                .filter(uuid=kwargs["uuid"])
                .first()
            )

        user = info.context.user
        public_lead = _get_lead_from_qs(get_public_lead_qs())
        if user is None or user.is_anonymous:
            return _return(public_lead, None, False)

        # We need to show/hide project title according to users membership.
        lead = public_lead or _get_lead_from_qs(Lead.objects.all())
        if lead is None:
            return _return(None, None, False)
        user_permissions = PP.get_permissions(lead.project, user)

        # NOTE: Without access to project (Project is passed for join-request action/status)
        if not len(user_permissions) > 0:
            return _return(public_lead, lead.project, False)

        # NOTE: With access to project (Project is passed for membership status)
        # Check if user have enough access for the resource.
        if public_lead:
            return _return(lead, lead.project, True)
        if PP.Permission.VIEW_ALL_LEAD in user_permissions:
            return _return(lead, lead.project, True)
        if (
            PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD in user_permissions
            and lead.confidentiality != Lead.Confidentiality.CONFIDENTIAL
        ):
            return _return(lead, lead.project, True)
        return _return(None, lead.project, True)
