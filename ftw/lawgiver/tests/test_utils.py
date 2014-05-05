from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.utils import get_specification
from ftw.lawgiver.utils import get_specification_for
from ftw.lawgiver.utils import get_workflow_for
from ftw.lawgiver.wdl.interfaces import ISpecification
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from unittest2 import TestCase


class TestUtils(TestCase):
    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager', 'Editor'])

        applyProfile(self.portal, 'ftw.lawgiver.tests:custom-workflow')
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Folder'], 'my_custom_workflow')
        wftool.setChainForPortalTypes(['Document'], '')

    def test_get_workflow_for_object(self):
        folder = create(Builder('folder'))
        workflow = get_workflow_for(folder)
        self.assertTrue(workflow)
        self.assertEquals('my_custom_workflow', workflow.id)

    def test_get_workflow_for_works_on_views(self):
        folder = create(Builder('folder'))
        view = folder.restrictedTraverse('@@sharing')
        workflow = get_workflow_for(view)
        self.assertTrue(workflow)
        self.assertEquals('my_custom_workflow', workflow.id)

    def test_get_workflow_for_returns_None_for_plone_site(self):
        self.assertIsNone(get_workflow_for(self.portal))

    def test_get_workflow_for_does_not_inherit_workflow(self):
        folder = create(Builder('folder'))  # has workflow
        page = create(Builder('page').within(folder))  # has no workflow
        self.assertIsNone(get_workflow_for(page))

    def test_get_specification(self):
        spec = get_specification('my_custom_workflow')
        self.assertTrue(spec,
                        'Could not find "my_custom_workflow" specification')

        self.assertTrue(ISpecification.providedBy(spec))
        self.assertEquals('My Custom Workflow', spec.title)

    def test_get_specification_returns_None_when_not_found(self):
        spec = get_specification('not a valid workflow id')
        self.assertIsNone(spec)

    def test_get_specification_for_object(self):
        folder = create(Builder('folder'))
        spec = get_specification_for(folder)
        self.assertTrue(spec)
        self.assertEquals('My Custom Workflow', spec.title)

    def test_get_specification_for_non_managed_object(self):
        self.assertIsNone(get_specification_for(self.portal))
