from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from unittest2 import TestCase
from zope.component import getUtility
from zope.i18n import translate


class TestActionGroupTranslations(TestCase):
    layer = LAWGIVER_INTEGRATION_TESTING

    def test_german(self):
        self.assert_action_groups_translated_to('de')

    def assert_action_groups_translated_to(self, language):
        action_group_registry = getUtility(IActionGroupRegistry)
        groups = action_group_registry.get_action_groups_for_workflow(None).keys()

        untranslated = [name for name in groups
                        if translate(name, target_language=language) == name]

        self.assertEquals(
            [], untranslated,
            'There action groups which are not translated to "{0}"'.format(language))
