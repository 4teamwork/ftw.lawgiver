from plone.app.workflow.interfaces import ISharingPageRole
from unittest2 import TestCase
from zope.component import getUtility
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING


class TestDynamicRolesUtility(TestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    def test_role_adapter_context_guessing_with_fallback(self):
        """The get_role_adapter guesses the context from the traversal
        stack (request.PARENTS), which might not be set correctly (e.g. in tests) and
        should fall back to the site root in this case.
        """

        utility = getUtility(ISharingPageRole, name='Reader')
        role_adapter = utility.get_role_adapter()
        self.assertTrue(role_adapter)
        self.assertEquals(self.layer['portal'], role_adapter.context)

    def test_role_title_when_fallback_necessary(self):
        utility = getUtility(ISharingPageRole, name='Reader')
        self.assertEquals('Can view', utility.title.default)
