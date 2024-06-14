from django.conf import settings


class Permalink:
    # TODO: Add test for permalink generation

    BASE_URL = f"{settings.HTTP_PROTOCOL}://{settings.DEEPER_FRONTEND_HOST}/permalink"

    @classmethod
    def project(cls, _id):
        return f"{cls.BASE_URL}/projects/{_id}"

    @classmethod
    def lead(cls, project_id, _id):
        return f"{cls.project(project_id)}/leads/{_id}"

    @classmethod
    def lead_share_view(cls, uuid):
        return f"{cls.BASE_URL}/leads-uuid/{uuid}"

    @classmethod
    def entry(cls, project_id, lead_id, _id):
        return f"{cls.lead(project_id, lead_id)}/entries/{_id}"

    @classmethod
    def ientry(cls, entry):
        return f"{cls.lead(entry.project_id, entry.lead_id)}/entries/{entry.id}"

    @classmethod
    def entry_comments(cls, project_id, lead_id, _id):
        return f"{cls.entry(project_id, lead_id, _id)}/comments/"

    @classmethod
    def ientry_comments(cls, entry):
        return f"{cls.ientry(entry)}/comments/"

    @classmethod
    def entry_comment(cls, project_id, lead_id, entry_id, _id):
        return f"{cls.entry(project_id, lead_id, entry_id)}/review-comments/{_id}/"

    @classmethod
    def ientry_comment(cls, comment):
        return f"{cls.ientry(comment.entry)}/review-comments/{comment.id}/"
