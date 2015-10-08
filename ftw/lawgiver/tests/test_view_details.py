from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import specdetails
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import plone
from ftw.testbrowser.pages import statusmessages
from operator import methodcaller
from unittest2 import TestCase
import os
import shutil
import transaction


TESTS_DIRECTORY = os.path.dirname(__file__)


BAR_DEFINITION_XML = os.path.abspath(os.path.join(
        TESTS_DIRECTORY,
        'profiles', 'bar', 'workflows', 'wf-bar', 'definition.xml'))

LOCALES_DIRECTORY = os.path.abspath(os.path.join(
        TESTS_DIRECTORY, 'locales'))


INVALID_WORKFLOW_DEFINITION_XML = os.path.abspath(os.path.join(
        TESTS_DIRECTORY,
        'profiles', 'spec-discovery', 'workflows', 'invalid-spec', 'definition.xml'))


BACKUP_FILES = [
    os.path.join(LOCALES_DIRECTORY, 'plone.pot'),
    os.path.join(LOCALES_DIRECTORY, 'en', 'LC_MESSAGES', 'plone.po'),
    ]


def remove_definition_xml(path=BAR_DEFINITION_XML):
    if os.path.exists(path):
        os.remove(path)


class TestBARSpecificationDetailsViewINSTALLED(TestCase):
    """Tests the specification details view of the workflow "wf-bar"
    with the workflow installed.
    """
    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        for path in BACKUP_FILES:
            shutil.copy2(path, '{0}.backup'.format(path))

    def tearDown(self):
        for path in BACKUP_FILES:
            shutil.move('{0}.backup'.format(path), path)

        remove_definition_xml()
        self.switch_language('en')

    def switch_language(self, lang_code):
        language_tool = getToolByName(self.layer['portal'], 'portal_languages')
        language_tool.manage_setLanguageSettings(
            lang_code,
            [lang_code],
            setUseCombinedLanguageCodes=False,
            startNeutral=False)
        transaction.commit()

    @browsing
    def test_details_view_heading(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        self.assertEquals('Bar Workflow', plone.first_heading())

    @browsing
    def test_spec_metadata_table(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        self.assertListEqual(
            [['Workflow ID:', 'wf-bar'],
             ['Specification file:',
              '..../profiles/bar/workflows/wf-bar/specification.txt'],
             ['Workflow definition file:',
              '..../profiles/bar/workflows/wf-bar/definition.xml'],
             ['Workflow installed:', 'No'],
             ['Translations location:', '..../locales']],
            specdetails.metadata())

    @browsing
    def test_specification_text(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        self.assertIn(
            'Status Published:',
            specdetails.specification_text(),
            'Seems the specification file is not printed in the view.')

    @browsing
    def test_action_groups(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        mapping = specdetails.action_groups()
        self.assertIn('view (view)', mapping,
                      'No action group "view" found.')

        self.assertIn('edit (edit)', mapping,
                      'No action group "edit" found.')

        self.assertIn(
            'Access contents information', mapping['view (view)'],
            'Permission "Access contents information" not in action'
            ' group "view"?')

        self.assertNotIn(
            'Modify portal content', mapping['view (view)'],
            'Permission "Modify portal content" should not be in action'
            ' group "view".')

        self.assertIn(
            'Modify portal content', mapping['edit (edit)'],
            'Permission "Modify portal content" not in action'
            ' group "edit"?')

    @browsing
    def test_german_action_groups(self, browser):
        self.switch_language('de')
        specdetails.visit('Bar Workflow (wf-bar)')
        mapping = specdetails.action_groups()
        self.assertIn('ansehen (view)', mapping.keys(),
                      'No action group "ansehen" found.')

    @browsing
    def test_unmanaged_permissions(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        unmanaged = specdetails.unmanaged_permissions()
        self.assertIn(
            'Plone Site Setup: Calendar', unmanaged,
            'Expected permission to be unmanaged.')

    @browsing
    def test_translations_pot(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        data = specdetails.translations_pot()

        self.assertMultiLineEqual(
            '\n'.join((
                    'msgid "Published"',
                    'msgstr ""',
                    '',
                    'msgid "wf-bar--ROLE--Editor"',
                    'msgstr ""',
                    '',
                    'msgid "wf-bar--ROLE--Manager"',
                    'msgstr ""',
                    )),
            data,
            'The translation template content is wrong.')

    @browsing
    def test_translations_po(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        data = specdetails.translations_po()

        self.assertMultiLineEqual(
            '\n'.join((
                    'msgid "Published"',
                    'msgstr "Published"',
                    '',
                    'msgid "wf-bar--ROLE--Editor"',
                    'msgstr "editor"',
                    '',
                    'msgid "wf-bar--ROLE--Manager"',
                    'msgstr "System Administrator"',
                    )),
            data,
            'The default translation content is wrong.')

    @browsing
    def test_write_workflow_XML(self, browser):
        self.assertFalse(os.path.exists(BAR_DEFINITION_XML),
                         'Expected %s to not exist yet.' % BAR_DEFINITION_XML)

        specdetails.visit('Bar Workflow (wf-bar)')
        specdetails.button_write().click()
        self.assertTrue(os.path.exists(BAR_DEFINITION_XML),
                        'Expected %s to exist now.' % BAR_DEFINITION_XML)

    @browsing
    def test_write_and_import(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        specdetails.button_write_and_import().click()

        def get_workflow():
            wftool = getToolByName(self.layer['portal'], 'portal_workflow')
            return wftool.get('wf-bar')

        self.assertEquals('Bar Workflow', get_workflow().title,
                          'Workflow title wrong after initial import.')

        # Change the workflow title in the database
        get_workflow().title = 'Wrong title'
        transaction.commit()

        # reimport with our button
        specdetails.button_write_and_import().click()
        self.assertEquals(
            'Bar Workflow', get_workflow().title,
            'Workflow title - write / reimport seems not working?')

        statusmessages.assert_message('Workflow wf-bar successfully imported.')

    @browsing
    def test_update_security(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        specdetails.button_reindex().click()
        statusmessages.assert_message('Security update: 0 objects updated.')

    @browsing
    def test_update_translations(self, browser):
        specdetails.visit('Bar Workflow (wf-bar)')
        specdetails.button_update_locales().click()
        statusmessages.assert_message(
            'wf-bar: The translations were updated in your locales directory.'
            ' You should now run bin/i18n-build')


class TestSpecificationDetailsViewBROKEN(TestCase):
    layer = SPECIFICATIONS_FUNCTIONAL

    @browsing
    def test_heading_shows_wfid(self, browser):
        specdetails.visit('spec-based-workflow')
        self.assertEquals('spec-based-workflow',
                          plone.first_heading(),
                          'Workflow title is wrong.')

    @browsing
    def test_error_messages_shown(self, browser):
        specdetails.visit('spec-based-workflow')
        statusmessages.assert_message(
            'The specification file could not be parsed:'
            ' Exactly one ini-style section is required,'
            ' containing the workflow title.')

    @browsing
    def test_buttons_not_shown(self, browser):
        specdetails.visit('spec-based-workflow')
        # on error, show no buttons
        self.assertFalse(
            specdetails.button_write(),
            'The Button "Write workflow definition" should not be visible')

        self.assertFalse(
            specdetails.button_write_and_import(),
            'The Button "Write and Import Workflow" should not be visible')

        self.assertFalse(
            specdetails.button_reindex(),
            'The Button "Update security settings" should not be visible')

    @browsing
    def test_definitionXML_not_touched_on_error(self, browser):
        with open(INVALID_WORKFLOW_DEFINITION_XML, 'w+') as file_:
            file_.write('some contents')

        specdetails.visit('Invalid Workflow (invalid-spec)')

        self.assertTrue(
            specdetails.button_write_and_import(),
            'The Button "Write and Import Workflow" in "Invalid Workflow"'
            ' should be visible but is not.')
        specdetails.button_write_and_import().click()

        self.assertGreater(
            os.path.getsize(INVALID_WORKFLOW_DEFINITION_XML), 0,
            'The definition.xml (%s) is empty, but it should not be touched'
            'since we had an error while generating.' % (
                INVALID_WORKFLOW_DEFINITION_XML))

        self.maxDiff = None
        self.assertEquals([], statusmessages.info_messages(),
                          'Expecting no "info" portal messages.')

        self.assertEquals(['invalid-spec: Error while generating the'
                           ' workflow: Action "viewX" is'
                           ' neither action group nor transition.'],
                          statusmessages.error_messages(),
                          'Expecting only the workflow generation error.')

        remove_definition_xml(INVALID_WORKFLOW_DEFINITION_XML)


DESTRUCTIVE_WF_DIR = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        'profiles', 'destructive', 'workflows', 'destructive-workflow'))


class TestDestructiveImport(TestCase):
    layer = SPECIFICATIONS_FUNCTIONAL

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

    @browsing
    def test_destruction_confirmation_on_import(self, browser):
        self.use_spec('foo')
        specdetails.visit('Destructive Workflow (destructive-workflow)')
        specdetails.button_write_and_import().click()
        statusmessages.assert_message(
            'Workflow destructive-workflow successfully imported.')
        self.assert_current_states('Foo')

        self.use_spec('bar')
        specdetails.visit('Destructive Workflow (destructive-workflow)')
        specdetails.button_write_and_import().click()

        # not yet updated
        self.assert_current_states('Foo')

        # confirmation dialog displayed
        self.assertEquals(
            'Importing this workflow renames or removes states.'
            ' Changing states can reset the workflow status of affected'
            ' objects to the initial state.',
            browser.css('.confirmation-message').first.text,)

        # No changes on cancel
        browser.find('I am on production').click()
        self.assert_current_states('Foo')

        specdetails.button_write_and_import().click()
        browser.find('I know what I am doing').click()
        statusmessages.assert_message(
            'Workflow destructive-workflow successfully imported.')
        self.assert_current_states('Foo', 'Bar')
