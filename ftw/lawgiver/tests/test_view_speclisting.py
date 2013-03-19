from ftw.lawgiver.testing import LAWGIVER_FUNCTIONAL_TESTING
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing import browser
from ftw.testing.pages import Plone
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


SPECIFICATIONS = SpecificationsLayer()


class TestSpecificationListingsView(TestCase):

    layer = SPECIFICATIONS

    def test_listing_specs(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        SpecsListing().open()
        self.assertTrue(browser().is_text_present('PETER'))
