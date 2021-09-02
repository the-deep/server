from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory

from quality_assurance.factories import EntryReviewCommentFactory, EntryReviewCommentTextFactory


class TestReviewCommentQuery(GraphQLTestCase):
    def test_review_comments_query(self):
        query = '''
            query MyQuery ($projectId: ID! $entryId: ID!) {
                project(id: $projectId) {
                    entry (id: $entryId) {
                        id
                        verifiedBy {
                            displayName
                            id
                        }
                        controlled
                        controlledChangedBy {
                            id
                            displayName
                        }
                        reviewComments {
                            commentType
                            createdAt
                            id
                            mentionedUsers {
                                displayName
                                id
                            }
                            textHistory {
                                createdAt
                                id
                                text
                            }
                        }
                    }
                }
            }
        '''

        user = UserFactory.create()
        user2, user3 = UserFactory.create_batch(2)
        analysis_framework = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=analysis_framework)
        lead = LeadFactory.create(project=project)
        entry = EntryFactory.create(
            project=project, analysis_framework=analysis_framework,
            lead=lead, controlled=True,
            controlled_changed_by=user2,
            verified_by=[user2, user3]
        )
        entry1 = EntryFactory.create(
            project=project, analysis_framework=analysis_framework,
            lead=lead,
        )

        review_comment1, review_comment2 = EntryReviewCommentFactory.create_batch(2, entry=entry, created_by=user)
        EntryReviewCommentFactory.create(entry=entry1, created_by=user)
        review_text1, review_text2 = EntryReviewCommentTextFactory.create_batch(2, comment=review_comment1)

        # -- Without login
        self.query_check(query, assert_for_error=True, variables={'projectId': project.id, 'entryId': entry.id})

        # -- With login
        self.force_login(user)

        # --- non-member user
        content = self.query_check(query, variables={'projectId': project.id, 'entryId': entry.id})
        self.assertEqual(content['data']['project']['entry'], None, content)

        # --- add-member in project
        project.add_member(user)
        content = self.query_check(query, variables={'projectId': project.id, 'entryId': entry.id})
        self.assertEqual(len(content['data']['project']['entry']['reviewComments']), 2, content)
        self.assertListIds(
            content['data']['project']['entry']['reviewComments'],
            [review_comment1, review_comment2],
            content
        )
        self.assertEqual(len(content['data']['project']['entry']['reviewComments'][1]['textHistory']), 2, content)
        self.assertListIds(
            content['data']['project']['entry']['reviewComments'][1]['textHistory'],
            [review_text1, review_text2],
            content
        )
        # lets check for the contolled in entry
        self.assertEqual(content['data']['project']['entry']['controlled'], True, content)
        self.assertEqual(content['data']['project']['entry']['controlledChangedBy']['id'], str(user2.id), content)
        self.assertEqual(len(content['data']['project']['entry']['verifiedBy']), 2, content)

        # lets query for another entry
        content = self.query_check(query, variables={'projectId': project.id, 'entryId': entry1.id})
        self.assertEqual(len(content['data']['project']['entry']['reviewComments']), 1, content)
