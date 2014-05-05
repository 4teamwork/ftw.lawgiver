from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.testbrowser import browser
from ftw.testbrowser import browsing
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from unittest2 import TestCase
import transaction


def javascript_resources():
    js_urls = filter(None, [node.attrib.get('src') for node in browser.css('script')])
    return ['/'.join(url.split('/')[6:]) for url in js_urls]


SHARING_JS_RESOURCE = '++resource++ftw.lawgiver-resources/sharing.js'
TICK = u'\u2713'


class TestSharingDescribeRoles(TestCase):
    layer = SPECIFICATIONS_FUNCTIONAL


    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager', 'Editor'])

        applyProfile(self.portal, 'ftw.lawgiver.tests:custom-workflow')
        wftool = getToolByName(self.portal, 'portal_workflow')
        wftool.setChainForPortalTypes(['Document'], 'my_custom_workflow')

        jstool = getToolByName(self.portal, 'portal_javascripts')
        jstool.setDebugMode(True)

    @browsing
    def test_javascript_loaded_on_lawgiverized_content(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page, view='@@sharing')

        self.assertIn(SHARING_JS_RESOURCE, javascript_resources(),
                      'The sharing javascript should be loaded on'
                      ' lawgiverized content.')

    @browsing
    def test_javascript_NOT_loaded_on_NON_lawgiverized_content(self, browser):
        folder = create(Builder('folder'))
        browser.login().visit(folder, view='@@sharing')
        self.assertNotIn(SHARING_JS_RESOURCE, javascript_resources(),
                         'The sharing javascript should NOT be loaded on'
                         ' Plone standard content without lawigver'
                         ' workflows.')

    @browsing
    def test_permissions_are_shown_per_status(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Action': 'Edit',
                       'Private': TICK,
                       'Pending': '',
                       'Published': ''}, table)

    @browsing
    def test_transitions_are_shown_per_status(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor-in-chief'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Action': 'Publish',
                       'Private': TICK,
                       'Pending': TICK,
                       'Published': ''}, table)

        self.assertIn({'Action': 'Reject',
                       'Private': '',
                       'Pending': TICK,
                       'Published': ''}, table)

        self.assertIn({'Action': 'Retract',
                       'Private': '',
                       'Pending': '',
                       'Published': TICK}, table)

    @browsing
    def test_translated_request(self, browser):
        page = create(Builder('page'))
        language_tool = getToolByName(self.layer['portal'], 'portal_languages')
        language_tool.manage_setLanguageSettings(
            'de', ['de'], setUseCombinedLanguageCodes=False, startNeutral=False)
        transaction.commit()

        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'Redaktor'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Aktion': 'Bearbeiten',
                       'Privat': TICK,
                       'Eingereicht': '',
                       'Publiziert': ''}, table)

        self.assertIn({'Aktion': 'Zur Publikation einreichen',
                       'Privat': TICK,
                       'Eingereicht': '',
                       'Publiziert': ''}, table)