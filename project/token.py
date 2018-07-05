from django.conf import settings
from deep.token import DeepTokenGenerator


class ProjectRequestTokenGenerator(DeepTokenGenerator):
    """
    Strategy object used to generate and check tokens for the project
    request mechanism.
    """
    key_salt = "projects.token.ProjectRequestTokenGenerator"
    secret = settings.SECRET_KEY
    reset_timeout_days = settings.PROJECT_REQUEST_RESET_TIMEOUT_DAYS

    def _make_hash_value(self, project_join_request, timestamp):
        """
        Hash the join request's primary key and some state that's sure to
        change after a join request to produce a token that invalidated when
        it's updated:
        1. The status field will change upon a project request accept.
        2. The responded_at field will be updated after a project join request
           accept.

        Failing those things, settings.PROJECT_REQUEST_RESET_TIMEOUT_DAYS
        eventually invalidates the token.
        """
        join_request = project_join_request['join_request']
        user = project_join_request['will_responded_by']

        # Truncate microseconds so that tokens are consistent even if the
        # database doesn't support microseconds.
        responded_at = '' if join_request.responded_at is None else\
            join_request.responded_at.replace(microsecond=0, tzinfo=None)
        return (
            str(join_request.pk) + str(user.pk) + join_request.status +
            str(responded_at) + str(timestamp)
        )


project_request_token_generator = ProjectRequestTokenGenerator()
