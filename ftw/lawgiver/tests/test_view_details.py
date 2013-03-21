from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import SpecDetails
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing import browser
from ftw.testing.pages import Plone
from operator import itemgetter
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import applyProfile
from unittest2 import TestCase
from zope.component import getMultiAdapter
import os
import transaction


class TestSpecificationDetailsView(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        SpecsListing().open()
        SpecsListing().get_specification_by_text(
            'Bar Workflow (wf-bar)').click()

    def tearDown(self):
        path = self.get_bar_XML_path()
        if os.path.exists(path):
            os.remove(path)

        super(TestSpecificationDetailsView, self).tearDown()

    def get_bar_XML_path(self):
        # The definition.xml may or may not exist - the path is returned
        # any way.
        portal = self.layer['portal']
        discovery = getMultiAdapter((portal, portal.REQUEST),
                                    IWorkflowSpecificationDiscovery)

        paths = [path for path in discovery.discover()
                if path.endswith('wf-bar/specification.txt')]
        assert len(paths) == 1, \
            'Failure in teardown when trying to delete the wf-bar xml'
        return paths[0].replace('specification.txt', 'definition.xml')

    def test_details_view_heading(self):
        self.assertEquals('Bar Workflow',
                          Plone().get_first_heading(),
                          'Workflow title is wrong.')

    def test_spec_metadata_table(self):
        metadata = SpecDetails().get_spec_metadata_table()

        self.assertEquals(
            ['Workflow ID:',
             'Specification file:',
             'Workflow definition file:'],
            map(itemgetter(0), metadata),
            'Metadata table has wrong headers.')

        metadata = dict(metadata)

        self.assertEquals(
            'wf-bar', metadata['Workflow ID:'],
            'Workflow ID in metadata table is wrong.')

        self.assertTrue(
            metadata['Specification file:'].endswith(
                '/wf-bar/specification.txt'),
            'Is the spec file (%s) not a specification.txt?' % (
                metadata['Specification file:']))

        self.assertTrue(
            metadata['Workflow definition file:'].endswith(
                '/wf-bar/definition.xml'),
            'Is the workflow file (%s) not a definition.xml?' % (
                metadata['Workflow definition file:']))

    def test_specification_text(self):
        self.assertIn(
            'Status Published:',
            SpecDetails().get_specification_text(),
            'Seems the specification file is not printed in the view.')

    def test_permission_mapping(self):
        mapping = SpecDetails().get_specification_mapping()
        self.assertIn('view', mapping,
                      'No action group "view" found.')

        self.assertIn('edit', mapping,
                      'No action group "edit" found.')

        self.assertIn(
            'Access contents information', mapping['view'],
            'Permission "Access contents information" not in action'
            ' group "view"?')

        self.assertNotIn(
            'Modify portal content', mapping['view'],
            'Permission "Modify portal content" should not be in action'
            ' group "view".')

        self.assertIn(
            'Modify portal content', mapping['edit'],
            'Permission "Modify portal content" not in action'
            ' group "edit"?')

    def test_unmanaged_permissions(self):
        unmanaged = SpecDetails().get_unmanaged_permissions()
        self.assertIn(
            'Plone Site Setup: Calendar', unmanaged,
            'Expected permission to be unmanaged.')

    def test_workflow_not_installed(self):
        Plone().assert_portal_message(
            'error', 'The workflow wf-bar is not installed yet.')
        self.assertTrue(
            SpecDetails().button_write(),
            'The Button "Write workflow definition" is not visible?')

        self.assertFalse(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" should not be visible')

        self.assertTrue(
            SpecDetails().button_reindex(),
            'The Button "Update security settings" is not visible?')

    def test_write_workflow_XML(self):
        path = self.get_bar_XML_path()
        self.assertFalse(os.path.exists(path),
                         'Expected %s to not exist yet.' % path)

        SpecDetails().button_write().click()
        self.assertTrue(os.path.exists(path),
                        'Expected %s to exist now.' % path)

    def test_write_and_import(self):
        def get_workflow():
            wftool = getToolByName(self.layer['portal'], 'portal_workflow')
            return wftool.get('wf-bar')

        # the workflow is not yet installed, therefore we don't see the button
        self.assertFalse(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" should not be visible')

        # we have no definition.xml yet - lets generate it first
        SpecDetails().button_write().click()

        # install the workflow (gs profile)
        applyProfile(self.layer['portal'], 'ftw.lawgiver.tests:bar')
        transaction.commit()

        # reload the page, now there should be the button
        browser().reload()
        self.assertTrue(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" should now be visible')

        self.assertEquals('Bar Workflow', get_workflow().title,
                          'Workflow title wrong after initial import.')

        # Change the workflow title in the database
        get_workflow().title = 'Wrong title'
        transaction.commit()

        # reimport with our button
        SpecDetails().button_write_and_import().click()
        self.assertEquals(
            'Bar Workflow', get_workflow().title,
            'Workflow title - write / reimport seems not working?')

        Plone().assert_portal_message(
            'info', 'Workflow wf-bar successfully imported.')

    def test_update_security(self):
        SpecDetails().button_reindex().click()
        Plone().assert_portal_message(
            'info', 'Security update: 0 objects updated.')


class TestSpecificationDetailsViewBROKEN(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        SpecsListing().open()

        # the workflow spec of "spec-based-workflow" is broken.
        SpecsListing().get_specification_by_text(
            'spec-based-workflow').click()

    def test_heading_shows_wfid(self):
        self.assertEquals('spec-based-workflow',
                          Plone().get_first_heading(),
                          'Workflow title is wrong.')

    def test_error_messages_shown(self):
        Plone().assert_portal_message(
            'error',
            'The specification file could not be parsed:'
            ' Exactly one ini-style section is required,'
            ' containing the workflow title.')

    def test_buttons_not_shown(self):
        # on error, show no buttons
        self.assertFalse(
            SpecDetails().button_write(),
            'The Button "Write workflow definition" should not be visible')

        self.assertFalse(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" should not be visible')

        self.assertFalse(
            SpecDetails().button_reindex(),
            'The Button "Update security settings" should not be visible')
