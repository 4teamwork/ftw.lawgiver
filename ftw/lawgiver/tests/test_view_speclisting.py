from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.helpers import cleanup_path
from ftw.lawgiver.tests.helpers import filestructure_snapshot
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import statusmessages
from operator import methodcaller
from plone.app.testing import SITE_OWNER_NAME
from unittest2 import TestCase
import os.path
import shutil


TESTS_PATH = os.path.dirname(__file__)

BACKUP_FILES = map(
    lambda path: os.path.join(TESTS_PATH, path), [
        'profiles/custom-workflow/workflows/my_custom_workflow/definition.xml',
        'locales/plone.pot',
        'locales/en/LC_MESSAGES/plone.po',
        ])


class TestSpecificationListingsView(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        self.snapshot = filestructure_snapshot(TESTS_PATH)
        for path in BACKUP_FILES:
            shutil.copy2(path, '{0}.backup'.format(path))

    def tearDown(self):
        for path in BACKUP_FILES:
            shutil.move('{0}.backup'.format(path), path)
        cleanup_path(TESTS_PATH, self.snapshot)

    @browsing
    def test_listing_spec_order(self, browser):
        browser.login(SITE_OWNER_NAME).visit(view='lawgiver-list-specs')
        self.assertItemsEqual(
            ['Bar Workflow (wf-bar)',
             'Foo Workflow (wf-foo)',
             'Invalid Workflow (invalid-spec)',
             'My Custom Workflow (my_custom_workflow)',
             'Role Translation Workflow (role-translation)',
             'another-spec-based-workflow',
             'spec-based-workflow'],
            browser.css('.specifications').first.terms)

    @browsing
    def test_listing_spec_descriptions(self, browser):
        browser.login(SITE_OWNER_NAME).visit(view='lawgiver-list-specs')

        self.assertEquals(
            {'another-spec-based-workflow': '',
             'My Custom Workflow (my_custom_workflow)':
                 'A three state publication workflow',
             'Role Translation Workflow (role-translation)':
                 'A one state workflow for testing role translation',
             'spec-based-workflow': '',
             'Bar Workflow (wf-bar)': 'Always published',
             'Foo Workflow (wf-foo)': 'Just for testing.',
             'Invalid Workflow (invalid-spec)': 'This workflow cannot be' +
             ' built because it has invalid statements.'},

            dict(browser.css('.specifications').first.items_text()))

    @browsing
    def test_spec_links_are_distinct(self, browser):
        browser.login(SITE_OWNER_NAME).visit(view='lawgiver-list-specs')
        links = [link.attrib.get('href')
                 for link in browser.css('.specifications dt a')]

        self.assertEquals(
            sorted(links), sorted(set(links)),
            'There are ambiguous spec links. Is the hashing wrong?')

    @browsing
    def test_update_all_sepcifications(self, browser):
        browser.login(SITE_OWNER_NAME).visit(view='lawgiver-list-specs')
        browser.find('Update all specifications').click()

        infos = map(methodcaller('replace', TESTS_PATH, '...'),
                    statusmessages.messages()['info'])
        self.assertIn(
            'role-translation: The workflow was generated to .../profiles'
            '/role-translation/workflows/role-translation/definition.xml.',
            infos)

        self.assertIn(
            'role-translation: The translations were updated in your'
            ' locales directory. You should now run bin/i18n-build',
            infos)

        self.assertIn(
            'invalid-spec: Error while generating the workflow:'
            ' Action "viewX" is neither action group nor transition.',
            statusmessages.messages()['error'])
