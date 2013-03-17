from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from unittest2 import TestCase
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.security.interfaces import IPermission


class TestPloneDefaultActionGroups(TestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    def test_no_unmapped_permissions(self):
        unmapped = []
        registry = getUtility(IActionGroupRegistry)

        # We use the the workflow_name __unmanaged__ since the permissions
        # we do not want to manage by default are registered on this fake
        # workflow so that we can track whether we are not managing them
        # by intention.

        for _name, permission in getUtilitiesFor(IPermission):
            if ',' in permission.title:
                # permissions with commas in the title are not supported
                # because it conflicts with the comma separated ZCML.
                # e.g. "Public, everyone can access"
                continue

            if not registry.get_action_group_for_permission(
                permission.title, workflow_name='__unmanaged__'):

                unmapped.append(permission.title)

        self.maxDiff = None
        self.assertEquals(
            [], unmapped,
            'There default Plone permissions which are not yet mapped'
            ' to action groups.')
