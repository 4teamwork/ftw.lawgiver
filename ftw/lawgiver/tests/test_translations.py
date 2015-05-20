from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.wdl.languages import LANGUAGES
from unittest2 import TestCase
from zope.component import getUtility
from zope.i18n import translate


class TestActionGroupTranslations(TestCase):
    layer = LAWGIVER_INTEGRATION_TESTING

    def test_translations(self):
        languages = LANGUAGES.keys()
        action_group_registry = getUtility(IActionGroupRegistry)
        groups = action_group_registry.get_action_groups_for_workflow(None).keys()

        untranslated = {}
        expected = {}

        for lang in languages:
            if lang == 'en':
                continue

            untranslated[lang] = [name for name in groups
                                  if translate(unicode(name),
                                               target_language=lang,
                                               domain='ftw.lawgiver') == name]
            expected[lang] = []

        # The "add folders" is defined in the testing layer just for testing purposes.
        for untranslated_groups in untranslated.values():
            if 'add folders' in untranslated_groups:
                untranslated_groups.remove('add folders')

        self.assertEquals(
            expected, untranslated,
            'There action groups which are not translated.')
