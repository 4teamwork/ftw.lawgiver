from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.testbrowser import browsing
from plone.app.testing import SITE_OWNER_NAME
from unittest2 import TestCase


class TestSpecificationListingsView(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

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
             'My Custom Workflow (my_custom_workflow)': \
                 'A three state publication workflow',
             'Role Translation Workflow (role-translation)': \
                 'A one state workflow for testing role translation',
             'spec-based-workflow': '',
             'Bar Workflow (wf-bar)': 'Always published',
             'Foo Workflow (wf-foo)': 'Just for testing.',
             'Invalid Workflow (invalid-spec)': 'This workflow cannot be built ' +\
                 'because it has invalid statements.'},

            dict(browser.css('.specifications').first.items_text()))

    @browsing
    def test_spec_links_are_distinct(self, browser):
        browser.login(SITE_OWNER_NAME).visit(view='lawgiver-list-specs')
        links = [link.attrib.get('href')
                 for link in browser.css('.specifications dt a')]

        self.assertEquals(
            sorted(links), sorted(set(links)),
            'There are ambiguous spec links. Is the hashing wrong?')
