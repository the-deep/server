from utils.graphene.tests import GraphQLTestCase
from project.factories import ProjectFactory
from project.migrations.rename_duplicate_project_name import _rename_duplicate_name
from project.migrations.set_istest_true_for_test_projects import _set_istest_true_for_test_projects
from project.models import Project


class TestProjectMigrations(GraphQLTestCase):
    def test_rename_duplicate_projects(self):
        project1, project2 = ProjectFactory.create_batch(2, title="Ukraine war")
        project3, project4 = ProjectFactory.create_batch(2, title="Nepal Food Crisis")
        project5, project6 = ProjectFactory.create_batch(2, title="Iran Bombblast")
        project9 = ProjectFactory(title='Iran Bombblast (2)')
        project10 = ProjectFactory(title='Iran Bombblast (3)')
        project11 = ProjectFactory(title='Japan Earthquake')
        project12 = ProjectFactory(title='Japan Hurricane')

        excepted_projects_name = {
            project1.pk: 'Ukraine war (1)',
            project2.pk: 'Ukraine war (2)',
            project3.pk: 'Nepal Food Crisis (1)',
            project4.pk: 'Nepal Food Crisis (2)',
            project5.pk: 'Iran Bombblast (1)',
            project6.pk: 'Iran Bombblast (4)',
            project9.pk: 'Iran Bombblast (2)',
            project10.pk: 'Iran Bombblast (3)',
            project11.pk: 'Japan Earthquake',
            project12.pk: 'Japan Hurricane',
        }

        _rename_duplicate_name(Project)

        for id, title in Project.objects.values_list('id', 'title'):
            assert excepted_projects_name[id] == title

    def test_set_istest_true_for_test_projects(self):
        project_titles = {
            'test project': True,
            'Test': True,
            'test project': True,
            'Testing project': True,
            'Test1': True,
            'Test2': True,
            'TestTestTest': True,
            'testing project': True,
            'test1 project': True,
            'UNHCR': False,
            'Relief Web': False,
        }
        for title in project_titles.keys():
            ProjectFactory(title=title)

        _set_istest_true_for_test_projects(Project)

        projects_qs = Project.objects.filter(title__in=project_titles.keys())
        assert projects_qs.count() == len(project_titles)
        # Check if the migration is as expected.
        for project in projects_qs:
            self.assertEqual(project.is_test, project_titles[project.title], project)
