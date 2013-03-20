from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import SpecDetails
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing.pages import Plone
from operator import itemgetter
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from unittest2 import TestCase


class TestSpecificationDetailsView(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        SpecsListing().open()
        SpecsListing().get_specification_by_text(
            'My Custom Workflow (my_custom_workflow)').click()

    def test_details_view_heading(self):
        self.assertEquals('My Custom Workflow',
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
            'my_custom_workflow', metadata['Workflow ID:'],
            'Workflow ID in metadata table is wrong.')

        self.assertTrue(
            metadata['Specification file:'].endswith(
                '/my_custom_workflow/specification.txt'),
            'Is the spec file (%s) not a specification.txt?' % (
                metadata['Specification file:']))

        self.assertTrue(
            metadata['Workflow definition file:'].endswith(
                '/my_custom_workflow/definition.xml'),
            'Is the workflow file (%s) not a definition.xml?' % (
                metadata['Workflow definition file:']))

    def test_specification_text(self):
        self.assertIn(
            'Status Private:',
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
