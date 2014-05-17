from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.testbrowser import browsing
from ftw.testbrowser.pages import plone
from plone.app.testing import SITE_OWNER_NAME
from unittest2 import TestCase


class TestControlPanel(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    @browsing
    def test_control_panel_link_points_to_spec_listing(self, browser):
        browser.login(SITE_OWNER_NAME).open(view='overview-controlpanel')
        links = browser.css('ul.configlets li').find('Lawgiver')
        self.assertTrue(links, 'The "Lawgiver" control panel link is missing.')

        links.first.click()
        self.assertEquals('lawgiver-list-specs', plone.view())
