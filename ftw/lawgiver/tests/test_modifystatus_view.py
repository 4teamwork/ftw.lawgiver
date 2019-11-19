from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.browser.modifystatus import ModifyStatusViewBase
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from unittest import TestCase


class TestModifyStatusViewBase(TestCase):
    layer = LAWGIVER_INTEGRATION_TESTING

    def setUp(self):
        super(TestModifyStatusViewBase, self).setUp()
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.wftool.setChainForPortalTypes(['Folder'], 'folder_workflow')

    def test_can_intercept_transitions(self):
        testcase = self
        folder = create(Builder('folder'))

        class MS(ModifyStatusViewBase):
            @ModifyStatusViewBase.intercept('publish')
            def abort_publication(self, context, transition):
                testcase.assertEqual(folder, context)
                testcase.assertEqual('publish', transition)
                return 'intercepted...'

        # the registered interception should be executed
        self.request.set('transition', 'publish')
        self.assertEqual('intercepted...', MS(folder, self.request)())

        # but non-interecepted transition should be redirected to content_status_modify
        self.assertIsNone(self.request.response.headers.get('location'))
        self.request.set('transition', 'submit')
        MS(folder, self.request)()
        self.assertEqual(
            '{}/content_status_modify?workflow_action=submit'.format(folder.absolute_url()),
            self.request.response.headers.get('location'))

    def test_execute_transition(self):
        folder = create(Builder('folder'))
        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

        ModifyStatusViewBase(folder, self.request).execute_transition(folder, 'publish')
        self.assertEqual('published', self.wftool.getInfoFor(folder, 'review_state'))

    def test_redirect_to_content_status_modify(self):
        folder = create(Builder('folder'))
        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

        ModifyStatusViewBase(folder, self.request).redirect_to_content_status_modify(
            folder, 'publish')
        self.assertEqual(
            '{}/content_status_modify?workflow_action=publish'.format(folder.absolute_url()),
            self.request.response.headers.get('location'))
        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

    def test_set_workflow_state(self):
        folder = create(Builder('folder'))
        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

        ModifyStatusViewBase(folder, self.request).set_workflow_state(folder, 'published')
        self.assertEqual('published', self.wftool.getInfoFor(folder, 'review_state'))

    def test_in_state(self):
        folder = create(Builder('folder'))
        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

        with ModifyStatusViewBase(folder, self.request).in_state(folder, 'published'):
            self.assertEqual('published', self.wftool.getInfoFor(folder, 'review_state'))

        self.assertEqual('visible', self.wftool.getInfoFor(folder, 'review_state'))

    def test_redirect_to(self):
        folder = create(Builder('folder'))
        self.assertIsNone(self.request.response.headers.get('location'))

        ModifyStatusViewBase(folder, self.request).redirect_to(folder)
        self.assertEqual(folder.absolute_url(), self.request.response.headers.get('location'))
