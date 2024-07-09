import graphene


class PrivateFileModuleType(graphene.Enum):
    ENTRY_ATTACHMENT = 'entry-attachment'
    LEAD_PREVIEW_ATTACHMENT = 'lead-preview-attachment'
