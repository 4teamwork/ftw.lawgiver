from Products.CMFCore.utils import getToolByName
from ftw.lawmaker.testing import LAWMAKER_FUNCTIONAL_TESTING
from unittest2 import TestCase


class TestInstallation(TestCase):

    layer = LAWMAKER_FUNCTIONAL_TESTING

    def test_gs_profile_installed(self):
        portal = self.layer['portal']
        portal_setup = getToolByName(portal, 'portal_setup')

        version = portal_setup.getLastVersionForProfile(
            'ftw.lawmaker:default')
        self.assertNotEqual(version, None)
        self.assertNotEqual(version, 'unknown')
