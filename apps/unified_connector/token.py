from django.conf import settings
from deep.token import DeepTokenGenerator

from .models import ConnectorLead


class ConnectorLeadExtractionTokenGenerator(DeepTokenGenerator):
    """
    Strategy object used to generate and check tokens for the project
    request mechanism.
    """
    key_salt = "projects.token.LeadExtractionTokenGenerator"
    secret = settings.SECRET_KEY
    reset_timeout_days = settings.CONNECTOR_LEAD_EXTRACTION_TOKEN_RESET_TIMEOUT_DAYS

    class FakeInstance():
        pk: str

    def make_token(self, instance: ConnectorLead):
        return super().make_token(instance)

    def _make_hash_value(self, connector_lead, timestamp):
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        return str(connector_lead.pk) + str(timestamp)


connector_lead_extraction_token_generator = ConnectorLeadExtractionTokenGenerator()
