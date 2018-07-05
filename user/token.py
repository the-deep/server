from django.conf import settings
from deep.token import DeepTokenGenerator


class UnsubscribeEmailTokenGenerator(DeepTokenGenerator):
    """
    Strategy object used to generate and check tokens for the unsubscribing
    user from receving email.
    """
    key_salt = "user.token.UnsubscribeEmailTokenGenerator"
    secret = settings.SECRET_KEY
    reset_timeout_days = 100

    def _make_hash_value(self, user, timestamp):
        """
        Hash the join request's primary key and some state that's sure to
        change after a join request to produce a token that invalidated when
        it's updated:
        1. Then link is valid if receive_email state is False

        Failing those things, this.reset_timeout_days
        eventually invalidates the token.
        """
        return (
            # FIXME: Add str(user.receive_email) here
            str(user.pk) + user.password +
            str(timestamp)
        )


unsubscribe_email_token_generator = UnsubscribeEmailTokenGenerator()
