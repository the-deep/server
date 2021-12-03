from utils.graphene.tests import GraphQLTestCase

from user.factories import UserFactory
from project.factories import ProjectFactory
from lead.factories import LeadFactory
from entry.factories import EntryFactory
from analysis_framework.factories import AnalysisFrameworkFactory
from lead.models import Lead

from quality_assurance.factories import (
    EntryReviewCommentFactory,
    EntryReviewCommentTextFactory
)


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
                            text
                        }
                        reviewCommentsCount
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
        review_text1 = EntryReviewCommentTextFactory.create(comment=review_comment1)

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
        self.assertEqual(content['data']['project']['entry']['reviewCommentsCount'], 2, content)
        self.assertEqual(len(content['data']['project']['entry']['reviewComments']), 2, content)
        self.assertListIds(
            content['data']['project']['entry']['reviewComments'],
            [review_comment1, review_comment2],
            content
        )
        self.assertEqual(
            content['data']['project']['entry']['reviewComments'][1]['text'],
            review_text1.text,
            content
        )

        # add another review_text for same review_comment
        review_text2 = EntryReviewCommentTextFactory.create(comment=review_comment1)
        content = self.query_check(query, variables={'projectId': project.id, 'entryId': entry.id})
        self.assertEqual(content['data']['project']['entry']['reviewCommentsCount'], 2, content)
        self.assertEqual(
            content['data']['project']['entry']['reviewComments'][1]['text'],
            review_text2.text,  # here latest text should be present
            content
        )

        # lets check for the contolled in entry
        self.assertEqual(content['data']['project']['entry']['controlled'], True, content)
        self.assertEqual(content['data']['project']['entry']['controlledChangedBy']['id'], str(user2.id), content)
        self.assertEqual(len(content['data']['project']['entry']['verifiedBy']), 2, content)

        # lets query for another entry
        content = self.query_check(query, variables={'projectId': project.id, 'entryId': entry1.id})
        self.assertEqual(content['data']['project']['entry']['reviewCommentsCount'], 1, content)
        self.assertEqual(len(content['data']['project']['entry']['reviewComments']), 1, content)

    def test_review_comments_project_scope_query(self):
        """
        Include permission check
        """
        query = '''
            query MyQuery ($projectId: ID! $reviewId: ID!) {
                project(id: $projectId) {
                    reviewComment(id: $reviewId) {
                        commentType
                        createdAt
                        createdBy {
                            id
                            firstName
                        }
                        id
                        mentionedUsers {
                            displayName
                            displayPictureUrl
                        }
                        textHistory {
                            createdAt
                            id
                            text
                        }
                    }
                }
            }
        '''

        user = UserFactory.create()
        analysis_framework = AnalysisFrameworkFactory.create()
        project = ProjectFactory.create(analysis_framework=analysis_framework)
        lead = LeadFactory.create(project=project)
        conf_lead = LeadFactory.create(project=project, confidentiality=Lead.Confidentiality.CONFIDENTIAL)
        entry = EntryFactory.create(project=project, analysis_framework=analysis_framework, lead=lead)
        conf_entry = EntryFactory.create(project=project, analysis_framework=analysis_framework, lead=conf_lead)

        review_comment = EntryReviewCommentFactory.create(entry=entry, created_by=user)
        conf_review_comment = EntryReviewCommentFactory.create(entry=conf_entry, created_by=user)
        review_text1, review_text2 = EntryReviewCommentTextFactory.create_batch(2, comment=review_comment)
        review_text_conf1, review_text_conf2 = EntryReviewCommentTextFactory.create_batch(2, comment=conf_review_comment)

        def _query_check(review_comment, **kwargs):
            return self.query_check(query, variables={'projectId': project.id, 'reviewId': review_comment.id}, **kwargs)

        # Without login
        _query_check(review_comment, assert_for_error=True)
        _query_check(conf_review_comment, assert_for_error=True)
        # With login
        self.force_login(user)
        # -- Without membership
        content = _query_check(review_comment)
        self.assertEqual(content['data']['project']['reviewComment'], None, content)
        # -- Without membership (confidential only)
        current_membership = project.add_member(user, role=self.project_role_reader_non_confidential)
        content = _query_check(review_comment)
        self.assertNotEqual(content['data']['project']['reviewComment'], None, content)
        self.assertEqual(len(content['data']['project']['reviewComment']['textHistory']), 2, content)
        self.assertListIds(
            content['data']['project']['reviewComment']['textHistory'],
            [review_text1, review_text2],
            content
        )
        content = _query_check(conf_review_comment)
        self.assertEqual(content['data']['project']['reviewComment'], None, content)
        # -- With membership (non-confidential only)
        current_membership.delete()
        project.add_member(user, role=self.project_role_reader)
        content = _query_check(review_comment)
        self.assertNotEqual(content['data']['project']['reviewComment'], None, content)
        content = _query_check(conf_review_comment)
        self.assertNotEqual(content['data']['project']['reviewComment'], None, content)
        self.assertEqual(len(content['data']['project']['reviewComment']['textHistory']), 2, content)
        self.assertListIds(
            content['data']['project']['reviewComment']['textHistory'],
            [review_text_conf1, review_text_conf2],
            content
        )
