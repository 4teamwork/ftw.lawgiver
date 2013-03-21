from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import SpecsListing
from ftw.testing import browser
from ftw.testing.pages import Plone
from ftw.testing.pages import PloneControlPanel
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from unittest2 import TestCase


class TestControlPanel(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def test_control_panel_entry(self):
        Plone().login(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        PloneControlPanel().open()
        self.assertIn('Lawgiver',
                      PloneControlPanel().get_control_panel_links())

        PloneControlPanel().get_control_panel_link('Lawgiver').click()
        self.assertEquals(SpecsListing().listing_url, browser().url,
                          'Lawgiver control panel link wrong')
