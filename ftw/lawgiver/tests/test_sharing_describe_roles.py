from Products.CMFCore.utils import getToolByName
from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests import helpers
from ftw.testbrowser import browser
from ftw.testbrowser import browsing
from ftw.testing import IS_PLONE_5
from plone.app.testing import TEST_USER_ID
from plone.app.testing import applyProfile
from plone.app.testing import setRoles
from plone.registry.interfaces import IRegistry
from unittest2 import TestCase
from zope.component import getUtility
import transaction


def javascript_resources(portal):
    js_urls = filter(None, [node.attrib.get('src')
                            for node in browser.css('script')])
    if IS_PLONE_5:
        return [url.replace(portal.absolute_url() + '/', '') for url in js_urls]
    return ['/'.join(url.split('/')[6:]) for url in js_urls]


SHARING_JS_RESOURCE = '++resource++ftw.lawgiver-resources/sharing.js'

if IS_PLONE_5:
    TICK = u'\xe2\x9c\x93'
else:
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

        if IS_PLONE_5:
            # Enable development of the Plone legacy JavaScript bundle.
            registry = getUtility(IRegistry)
            registry['plone.resources.development'] = True
            registry['plone.bundles/plone-legacy.develop_javascript'] = True
            transaction.commit()

        browser.login().visit(page, view='@@sharing')

        self.assertIn(SHARING_JS_RESOURCE, javascript_resources(self.layer['portal']),
                      'The sharing javascript should be loaded on'
                      ' lawgiverized content.')

    @browsing
    def test_javascript_NOT_loaded_on_NON_lawgiverized_content(self, browser):
        folder = create(Builder('folder'))
        browser.login().visit(folder, view='@@sharing')
        self.assertNotIn(SHARING_JS_RESOURCE, javascript_resources(self.layer['portal']),
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
    def test_permissions_from_general_statements_are_included(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Action': 'Add',
                       'Private': TICK,
                       'Pending': TICK,
                       'Published': TICK}, table)

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
    def test_general_role_inheritance_is_respected(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Action': 'View',
                       'Private': TICK,
                       'Pending': TICK,
                       'Published': TICK}, table)

    @browsing
    def test_status_specific_role_inheritance_is_respected(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor-in-chief'})
        table = browser.css('table').first.dicts()

        self.assertIn({'Action': 'View',
                       'Private': TICK,
                       'Pending': TICK,
                       'Published': TICK}, table)

        self.assertIn({'Action': 'Retract',
                       'Private': '',
                       'Pending': '',
                       'Published': TICK}, table)

    @browsing
    def test_role_description_is_displayed_when_defined(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor-in-chief'})
        description = browser.css('.role-description').first.text

        # This description is set through translations in the Plone domain.
        self.assertEquals('The editor-in-chief reviews and publishes content.',
                          description)

    @browsing
    def test_role_description_is_not_displayed_when_missing(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              data={'role': 'editor'})
        self.assertFalse(browser.css('.role-description'),
                         'Did not expect that "editor" has a role description.')

    @browsing
    def test_translated_request(self, browser):
        page = create(Builder('page'))
        helpers.switch_language(self.layer['portal'], 'de')

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

    @browsing
    def test_error_message_when_no_role_Found(self, browser):
        page = create(Builder('page'))
        browser.login().visit(page,
                              view='lawgiver-sharing-describe-role',
                              # "Reviewer" is not a spec role and is never displayd
                              # in the sharing view.
                              data={'role': 'Reviewer'})

        self.assertEquals('Could not find any information about this role.',
                          browser.css('p.error').first.text)
