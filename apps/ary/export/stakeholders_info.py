from ary.models import MetadataField


STAKEHOLDERS_SOURCE_TYPES = [MetadataField.ORGANIZATIONS]

default_values = {
    'stakeholders': None,
}

from assessment_registry.models import AssessmentRegistryOrganization
def get_stakeholders_info(assessment):
    stakeholders_info=[
        {
            'name': org.organization.title,
            'type': org.get_organization_type_display()
        }for org in AssessmentRegistryOrganization.objects.filter(assessment_registry=assessment)
    ] #TODO : Add Dataloaders

    return {
        'stakeholders': stakeholders_info,
    }
