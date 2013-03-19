from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.interfaces import ILawgiverLayer
from ftw.lawgiver.testing import LAWGIVER_FUNCTIONAL_TESTING
from plone.browserlayer.utils import registered_layers
from unittest2 import TestCase


class TestInstallation(TestCase):

    layer = LAWGIVER_FUNCTIONAL_TESTING

    def test_gs_profile_installed(self):
        portal = self.layer['portal']
        portal_setup = getToolByName(portal, 'portal_setup')

        version = portal_setup.getLastVersionForProfile(
            'ftw.lawgiver:default')
        self.assertNotEqual(version, None)
        self.assertNotEqual(version, 'unknown')

    def test_request_layer_active(self):
        layers = registered_layers()
        self.assertIn(ILawgiverLayer, layers,
                      'Browser layer "ILawgiverLayer" is not installed.')
