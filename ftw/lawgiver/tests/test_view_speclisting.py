from ftw.lawgiver.testing import LAWGIVER_FUNCTIONAL_TESTING
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing.pages import Plone
from operator import methodcaller
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from unittest2 import TestCase
from zope.configuration import xmlconfig


class SpecificationsLayer(PloneSandboxLayer):

    defaultBases = (LAWGIVER_FUNCTIONAL_TESTING, )

    def setUpZope(self, app, configurationContext):
        import ftw.lawgiver.tests

        xmlconfig.file('spec-discovery.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('custom-workflow.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)


SPECIFICATIONS = SpecificationsLayer()


class TestSpecificationListingsView(TestCase):

    layer = SPECIFICATIONS

    def test_listing_spec_order(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecsListing().open()

        specs = SpecsListing().get_specifications()
        self.assertEquals(
            ['My Custom Workflow (my_custom_workflow)',
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
             'spec-based-workflow': ''},

            dict(map(lambda spec: (spec.link_text(), spec.description()),
                     specs)))
