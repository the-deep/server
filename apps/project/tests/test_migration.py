from utils.graphene.tests import GraphQLTestCase
from project.factories import ProjectFactory
from project.migrations.rename_duplicate_project_name import _rename_duplicate_name
from project.models import Project


class TestProjectSchema(GraphQLTestCase):
    def test_rename_duplicate_projects(self):
        project1, project2 = ProjectFactory.create_batch(2, title="Ukraine war")
        project3, project4 = ProjectFactory.create_batch(2, title="Nepal Food Crisis")
        project5, project6 = ProjectFactory.create_batch(2, title="Iran Bombblast")
        project9 = ProjectFactory(title='Iran Bombblast (2)')
        project10 = ProjectFactory(title='Iran Bombblast (3)')
        project11 = ProjectFactory(title='Japan Earthquake')
        project12 = ProjectFactory(title='Japan Hurricane')

        _rename_duplicate_name(Project)

        title_list_1 = [p.title for p in Project.objects.filter(id__in=[project1.id, project2.id])]
        title_list_2 = [p.title for p in Project.objects.filter(id__in=[project3.id, project4.id])]
        title_list_3 = [
            p.title for p in Project.objects.filter(id__in=[project5.id, project6.id, project9.id, project10.id])
        ]
        title_list_4 = [p.title for p in Project.objects.filter(id__in=[project11.id, project12.id])]
        self.assertEqual(title_list_1, ['Ukraine war (1)', 'Ukraine war (2)'])
        self.assertEqual(title_list_2, ['Nepal Food Crisis (1)', 'Nepal Food Crisis (2)'])
        self.assertEqual(
            sorted(title_list_3),
            sorted(['Iran Bombblast (1)', 'Iran Bombblast (2)', 'Iran Bombblast (3)', 'Iran Bombblast (4)'])
        )
        self.assertEqual(sorted(title_list_4), sorted(['Japan Earthquake', 'Japan Hurricane']))
