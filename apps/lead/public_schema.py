import graphene

from deep.permissions import ProjectPermissions as PP
from utils.graphene.enums import EnumDescription
from gallery.schema import PublicGalleryFileType

from .models import Lead
from .schema import LeadSourceTypeEnum


def get_public_lead_qs():
    return Lead.objects.filter(
        project__has_publicly_viewable_leads=True,
        confidentiality=Lead.Confidentiality.UNPROTECTED,
    )


class PublicLeadType(graphene.ObjectType):
    uuid = graphene.UUID(required=True)
    project_title = graphene.String(required=True)
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
        return root.project.title

    @staticmethod
    def resolve_created_by_display_name(root, info, **_):
        return root.created_by and root.created_by.get_display_name()

    @staticmethod
    def resolve_source_title(root, info, **_):
        return root.source and root.source.data.title


class Query:
    public_lead = graphene.Field(
        PublicLeadType,
        uuid=graphene.UUID(required=True),
    )

    @staticmethod
    def resolve_public_lead(root, info, **kwargs):
        def _get_lead(qs):
            return qs\
                .select_related(
                    'project',
                    'created_by',
                    'source',
                    'source__parent',
                ).filter(uuid=kwargs['uuid']).first()
        user = info.context.user
        if user is None or user.is_anonymous:
            return _get_lead(get_public_lead_qs())

        lead = _get_lead(Lead.objects)
        if lead is None:
            return
        user_permissions = PP.get_permissions(lead.project, user)
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
            return lead
