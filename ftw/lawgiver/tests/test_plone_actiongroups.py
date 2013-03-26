from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from unittest2 import TestCase
from zope.component import getUtility


class TestPloneDefaultActionGroups(TestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    def test_no_unmapped_permissions(self):
        unmapped = []
        registry = getUtility(IActionGroupRegistry)

        # We use the the workflow_name __unmanaged__ since the permissions
        # we do not want to manage by default are registered on this fake
        # workflow so that we can track whether we are not managing them
        # by intention.

        for item in self.layer['portal'].ac_inherited_permissions(1):
            permission = item[0]

            if ',' in permission:
                # permissions with commas in the title are not supported
                # because it conflicts with the comma separated ZCML.
                # e.g. "Public, everyone can access"
                continue

            if not registry.get_action_group_for_permission(
                permission, workflow_name='__unmanaged__'):

                unmapped.append(permission)

        self.maxDiff = None
        self.assertEquals(
            [], unmapped,
            'There are default Plone permissions which are not yet mapped'
            ' to action groups.')
