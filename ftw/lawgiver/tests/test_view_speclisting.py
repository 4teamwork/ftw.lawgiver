from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing.pages import Plone
from operator import methodcaller
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from unittest2 import TestCase


class TestSpecificationListingsView(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def test_listing_spec_order(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecsListing().open()

        specs = SpecsListing().get_specifications()
        self.assertEquals(
            ['Bar Workflow (wf-bar)',
             'Foo Workflow (wf-foo)',
             'Invalid Workflow (invalid-spec)',
             'My Custom Workflow (my_custom_workflow)',
             'Role Translation Workflow (role-translation)',
             'another-spec-based-workflow',
             'spec-based-workflow'],

            map(methodcaller('link_text'), specs),

            'Workflow specs links in wrong order or wrong amount.')

    def test_listing_spec_descriptions(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecsListing().open()

        specs = SpecsListing().get_specifications()
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

            dict(map(lambda spec: (spec.link_text(), spec.description()),
                     specs)))

    def test_spec_links_are_distinct(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecsListing().open()

        specs = SpecsListing().get_specifications()
        links = map(methodcaller('link_href'), specs)

        self.assertEquals(
            sorted(links), sorted(set(links)),
            'There are ambiguous spec links. Is the hashing wrong?')
