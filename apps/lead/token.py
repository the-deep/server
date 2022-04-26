from django.conf import settings
from deep.token import DeepTokenGenerator


class LeadExtractionTokenGenerator(DeepTokenGenerator):
    """
    Strategy object used to generate and check tokens for the project
    request mechanism.
    """
    key_salt = "projects.token.LeadExtractionTokenGenerator"
    secret = settings.SECRET_KEY
    reset_timeout_days = settings.LEAD_EXTRACTION_TOKEN_RESET_TIMEOUT_DAYS

    def _make_hash_value(self, lead, timestamp):
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        return str(lead.pk) + str(timestamp)


lead_extraction_token_generator = LeadExtractionTokenGenerator()
