from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.interfaces import IDynamicRoleAdapter
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import sharing
from ftw.testbrowser import browsing
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from unittest2 import TestCase
from zope.component import getMultiAdapter


class TestSharingRoleTranslation(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager', 'Editor'])

    @browsing
    def test_default_role_translation_for_default_workflows(self, browser):
        document = create(Builder('document'))
        sharing.visit(document)

        self.assertEquals(
            ['Can add', 'Can edit', 'Can review', 'Can view'],
            sharing.role_labels())

    @browsing
    def test_custom_role_translation_per_workflow(self, browser):
        applyProfile(self.portal, 'ftw.lawgiver.tests:role-translation')
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], 'role-translation')

        document = create(Builder('document'))
        sharing.visit(document)

        self.assertEquals(
            ['Can add', 'Can view', 'editor', 'editor-in-chief'],
            sharing.role_labels())

    def test_custom_role_translation_per_workflow_when_context_is_view(self):
        # Dependenging on what is traversed, the role utility may guess
        # the view from the request as context.
        applyProfile(self.portal, 'ftw.lawgiver.tests:role-translation')
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], 'role-translation')

        document = create(Builder('document'))
        view = document.restrictedTraverse('folder_contents')

        adapter = getMultiAdapter((view, document.REQUEST),
                                  IDynamicRoleAdapter,
                                  name='Reader')
        self.assertEquals('role-translation--ROLE--Reader',
                          adapter.get_title())
