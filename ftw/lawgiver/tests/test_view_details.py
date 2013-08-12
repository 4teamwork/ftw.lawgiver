from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import SpecDetails
from ftw.lawgiver.tests.pages import SpecDetailsConfirmation
from ftw.testing.pages import Plone
from operator import itemgetter
from operator import methodcaller
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import applyProfile
from unittest2 import TestCase
import os
import shutil
import transaction


BAR_DEFINITION_XML = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'profiles', 'bar', 'workflows', 'wf-bar', 'definition.xml'))

INVALID_WORKFLOW_DEFINITION_XML = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'profiles', 'spec-discovery', 'workflows', 'invalid-spec', 'definition.xml'))


def remove_definition_xml(path=BAR_DEFINITION_XML):
    if os.path.exists(path):
        os.remove(path)


class TestBARSpecificationDetailsViewINSTALLED(TestCase):
    """Tests the specification details view of the workflow "wf-bar"
    with the workflow installed.
    """

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

        # generate the workflow and import it
        SpecDetails().open('Bar Workflow (wf-bar)')
        SpecDetails().button_write().click()
        applyProfile(self.layer['portal'], 'ftw.lawgiver.tests:bar')
        remove_definition_xml()
        transaction.commit()

        SpecDetails().open('Bar Workflow (wf-bar)')

    def tearDown(self):
        remove_definition_xml()

    def test_details_view_heading(self):
        self.assertEquals('Bar Workflow',
                          Plone().get_first_heading(),
                          'Workflow title is wrong.')

    def test_spec_metadata_table(self):
        metadata = SpecDetails().get_spec_metadata_table()

        self.assertEquals(
            ['Workflow ID:',
             'Specification file:',
             'Workflow definition file:',
             'Workflow installed:'],
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

        self.assertEquals(
            'Yes', metadata['Workflow installed:'],
            'The workflow IS installed, but it says that it is NOT.')

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

    def test_translations_pot(self):
        data = SpecDetails().get_translations_pot().strip()

        self.assertMultiLineEqual(
            '\n'.join((
                    'msgid "wf-bar--ROLE--Editor"',
                    'msgstr ""',
                    '',
                    'msgid "wf-bar--ROLE--Manager"',
                    'msgstr ""',
                    '',
                    'msgid "wf-bar--STATUS--published"',
                    'msgstr ""',
                    )),
            data,
            'The translation template content is wrong.')

    def test_translations_po(self):
        data = SpecDetails().get_translations_po().strip()

        self.assertMultiLineEqual(
            '\n'.join((
                    'msgid "wf-bar--ROLE--Editor"',
                    'msgstr "editor"',
                    '',
                    'msgid "wf-bar--ROLE--Manager"',
                    'msgstr "System Administrator"',
                    '',
                    'msgid "wf-bar--STATUS--published"',
                    'msgstr "Published"',
                    )),
            data,
            'The default translation content is wrong.')

    def test_write_workflow_XML(self):
        self.assertFalse(os.path.exists(BAR_DEFINITION_XML),
                         'Expected %s to not exist yet.' % BAR_DEFINITION_XML)

        SpecDetails().button_write().click()
        self.assertTrue(os.path.exists(BAR_DEFINITION_XML),
                        'Expected %s to exist now.' % BAR_DEFINITION_XML)

    def test_write_and_import(self):
        def get_workflow():
            wftool = getToolByName(self.layer['portal'], 'portal_workflow')
            return wftool.get('wf-bar')

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


class TestBARSpecificationDetailsViewNOT_INSTALLED(TestCase):
    """Tests the specification details view of the workflow "wf-bar"
    with the workflow NOT installed.
    """

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecDetails().open('Bar Workflow (wf-bar)')

    def tearDown(self):
        remove_definition_xml()

    def test_spec_metadata_table(self):
        metadata = SpecDetails().get_spec_metadata_table()

        self.assertEquals(
            ['Workflow ID:',
             'Specification file:',
             'Workflow definition file:',
             'Workflow installed:'],
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

        self.assertEquals(
            'No', metadata['Workflow installed:'],
            'The workflow is NOT installed, but it says that it IS.')

    def test_workflow_not_installed(self):
        Plone().assert_portal_message(
            'warning',
            'The workflow wf-bar is not installed yet.'
            ' Installing the workflow with the "Write and Import Workflow"'
            ' button does not configure the policy, so no portal type will'
            ' have this workflow.')

        self.assertTrue(
            SpecDetails().button_write(),
            'The Button "Write workflow definition" is not visible?')

        self.assertTrue(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" is not visible?')

        self.assertTrue(
            SpecDetails().button_reindex(),
            'The Button "Update security settings" is not visible?')

    def test_write_and_import(self):
        def get_workflow():
            wftool = getToolByName(self.layer['portal'], 'portal_workflow')
            return wftool.get('wf-bar')

        self.assertEquals(None, get_workflow(),
                          'Expected workflow wf-bar not to be installed, but it was')
        self.assertFalse(SpecDetails().is_workflow_installed(),
                         'Details view says the workflow is installed, but it is not')

        SpecDetails().button_write_and_import().click()
        self.assertEquals(
            'Bar Workflow', get_workflow().title,
            'Workflow title - write / reimport seems not working?')

        Plone().assert_portal_message(
            'info', 'Workflow wf-bar successfully imported.')

        self.assertTrue(
            SpecDetails().is_workflow_installed(),
            'The workflow should be installed, but the details view says it is not')


class TestSpecificationDetailsViewBROKEN(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def test_heading_shows_wfid(self):
        SpecDetails().open('spec-based-workflow')
        self.assertEquals('spec-based-workflow',
                          Plone().get_first_heading(),
                          'Workflow title is wrong.')

    def test_error_messages_shown(self):
        SpecDetails().open('spec-based-workflow')
        Plone().assert_portal_message(
            'error',
            'The specification file could not be parsed:'
            ' Exactly one ini-style section is required,'
            ' containing the workflow title.')

    def test_buttons_not_shown(self):
        SpecDetails().open('spec-based-workflow')
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

    def test_definitionXML_not_touched_on_error(self):
        with open(INVALID_WORKFLOW_DEFINITION_XML, 'w+') as file_:
            file_.write('some contents')

        SpecDetails().open('Invalid Workflow (invalid-spec)')

        self.assertTrue(
            SpecDetails().button_write_and_import(),
            'The Button "Write and Import Workflow" in "Invalid Workflow"'
            ' should be visible but is not.')
        SpecDetails().button_write_and_import().click()

        self.assertGreater(
            os.path.getsize(INVALID_WORKFLOW_DEFINITION_XML), 0,
            'The definition.xml (%s) is empty, but it should not be touched'
            'since we had an error while generating.' % (
                INVALID_WORKFLOW_DEFINITION_XML))

        self.maxDiff = None
        self.assertEquals([], Plone().portal_text_messages()['info'],
                          'Expecting no "info" portal messages.')

        self.assertEquals(['Error while generating the workflow: Action "viewX" is'
                           ' neither action group nor transition.'],
                          Plone().portal_text_messages()['error'],
                          'Expecting only the workflow generation error.')

        remove_definition_xml(INVALID_WORKFLOW_DEFINITION_XML)


DESTRUCTIVE_WF_DIR = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'profiles', 'destructive', 'workflows', 'destructive-workflow'))


class TestDestructiveImport(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)

    def tearDown(self):
        paths = [
            os.path.join(DESTRUCTIVE_WF_DIR, 'specification.txt'),
            os.path.join(DESTRUCTIVE_WF_DIR, 'definition.xml'),]

        for path in paths:
            if os.path.exists(path):
                os.remove(path)

    def use_spec(self, postfix):
        src = os.path.join(DESTRUCTIVE_WF_DIR, 'specification-%s.txt' % (
                postfix))
        dest = os.path.join(DESTRUCTIVE_WF_DIR, 'specification.txt')

        shutil.copyfile(src, dest)

    def get_states(self):
        wftool = getToolByName(self.layer['portal'], 'portal_workflow')
        states = map(methodcaller('title'),
                     wftool.get('destructive-workflow').states)
        return states

    def assert_current_states(self, *postfixes):
        states = self.get_states()
        expected = ['Destructive-Workflow--Status--%s' % postfix
                    for postfix in postfixes]

        self.assertEquals(
            set(expected), set(states),
            'Workflow states of destructive workflow not as expected')

    def test_destruction_confirmation_on_import(self):
        self.use_spec('foo')
        SpecDetails().open('Destructive Workflow (destructive-workflow)')
        SpecDetails().button_write_and_import().click()
        Plone().assert_portal_message(
            'info', 'Workflow destructive-workflow successfully imported.')
        self.assert_current_states('Foo')

        self.use_spec('bar')
        SpecDetails().open('Destructive Workflow (destructive-workflow)')
        SpecDetails().button_write_and_import().click()

        # not yet updated
        self.assert_current_states('Foo')

        # confirmation dialog displayed
        self.assertTrue(
            SpecDetailsConfirmation().is_confirmation_dialog_opened(),
            'Expected to be on a confirmation dialog, but was not')

        self.assertEquals(
            'Importing this workflow renames or removes states.'
            ' Changing states can reset the workflow status of affected'
            ' objects to the initial state.',
            SpecDetailsConfirmation().get_confirmation_dialog_text())

        # No changes on cancel
        SpecDetailsConfirmation().cancel()
        self.assert_current_states('Foo')

        SpecDetails().button_write_and_import().click()
        SpecDetailsConfirmation().confirm()
        Plone().assert_portal_message(
            'info', 'Workflow destructive-workflow successfully imported.')
        self.assert_current_states('Foo', 'Bar')
