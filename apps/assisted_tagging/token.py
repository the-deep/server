from django.conf import settings
from deep.token import DeepTokenGenerator

from .models import DraftEntry


class DraftEntryExtractionTokenGenerator(DeepTokenGenerator):
    """
    Strategy object used to generate and check tokens for the project
    request mechanism.
    """
    key_salt = "projects.token.DraftEntryTokenGenerator"
    secret = settings.SECRET_KEY
    reset_timeout_days = settings.DRAFT_ENTRY_EXTRACTION_TIMEOUT_DAYS

    def make_token(self, instance: DraftEntry):
        return super().make_token(instance)

    def _make_hash_value(self, lead, timestamp):
        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        return str(lead.pk) + str(timestamp)


draft_entry_extraction_token_generator = DraftEntryExtractionTokenGenerator()
