import graphene

from deep.permissions import ProjectPermissions as PP
from utils.graphene.enums import EnumDescription
from gallery.schema import PublicGalleryFileType
from project.public_schema import PublicProjectWithMembershipData

from .models import Lead
from .schema import LeadSourceTypeEnum


def get_public_lead_qs():
    return Lead.objects.filter(
        project__has_publicly_viewable_leads=True,
        confidentiality=Lead.Confidentiality.UNPROTECTED,
    )


class PublicLeadDetailType(graphene.ObjectType):
    uuid = graphene.UUID(required=True)
    project_title = graphene.String()
    created_by_display_name = graphene.String()
    source_title = graphene.String()
    published_on = graphene.Date()

    source_type = graphene.Field(LeadSourceTypeEnum, required=True)
    source_type_display = EnumDescription(source='get_source_type_display', required=True)
    text = graphene.String()
    url = graphene.String()
    attachment = graphene.Field(PublicGalleryFileType)

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
            print('>>', lead, project, project and project.is_private, has_access)
            if (project and project.is_private) and not has_access:
                _project = None
            if lead:
                lead.has_project_access = has_access
            return {
                'project': _project,
                'lead': lead,
            }

        def _get_lead_from_qs(qs):
            return qs\
                .select_related(
                    'project',
                    'created_by',
                    'source',
                    'source__parent',
                ).filter(uuid=kwargs['uuid']).first()

        user = info.context.user
        if user is None or user.is_anonymous:
            lead = _get_lead_from_qs(get_public_lead_qs())
            return _return(lead, None, False)

        lead = _get_lead_from_qs(Lead.objects.all())
        if lead is None:
            return _return(None, None, False)
        user_permissions = PP.get_permissions(lead.project, user)
        has_access = len(user_permissions) > 0
        if (
            PP.Permission.VIEW_ALL_LEAD in user_permissions or
            (
                PP.Permission.VIEW_ONLY_UNPROTECTED_LEAD in user_permissions and
                lead.confidentiality != Lead.Confidentiality.CONFIDENTIAL
            ) or (
                lead.confidentiality == Lead.Confidentiality.UNPROTECTED and  # IS public
                lead.project.has_publicly_viewable_leads  # Project allows to share pubilc leads
            )
        ):
            return _return(lead, lead.project, has_access)
        return _return(None, lead.project, has_access)
