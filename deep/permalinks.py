from django.conf import settings


class Permalink:
    # TODO: Add test for permalink generation

    BASE_URL = f'{settings.HTTP_PROTOCOL}://{settings.DEEPER_FRONTEND_HOST}/permalink'

    def project(self, _id):
        return f'{self.BASE_URL}/projects/{_id}'

    def lead(self, project_id, _id):
        return f'{self.project(project_id)}/leads/{_id}'

    def entry(self, project_id, lead_id, _id):
        return f'{self.lead(project_id, lead_id)}/entries/{_id}'
