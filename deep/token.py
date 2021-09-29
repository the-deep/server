from datetime import date

from django.conf import settings
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.crypto import constant_time_compare
from django.utils.http import base36_to_int


class DeepTokenGenerator(PasswordResetTokenGenerator):
    """
    Strategy object used to generate and check tokens for the deep models
    mechanism.
    """
    # key_salt = "deep.token.DeepTokenGenerator"
    reset_timeout_days = settings.TOKEN_DEFAULT_RESET_TIMEOUT_DAYS
    secret = settings.SECRET_KEY

    class Meta:
        abstract = True

    def check_token(self, model, token):
        """
        Check that a model token is correct for a given model
        """
        if not (model and token):
            return False
        # Parse the token
        try:
            ts_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            ts = base36_to_int(ts_b36)
        except ValueError:
            return False

        # Check that the timestamp/uid has not been tampered with
        if not constant_time_compare(
                self._make_token_with_timestamp(model, ts),
                token
        ):
            return False

        # Check TIMEOUT
        if (
                self._num_days(self._today()) - ts
        ) > self.reset_timeout_days:
            return False

        return True

    def _make_hash_value(self, model, timestamp):
        raise Exception(
            "No _make_hash_value defined for Class: " + type(self).__name__
        )

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        return date.today()
