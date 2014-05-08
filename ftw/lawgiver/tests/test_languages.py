from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import EqualityTestCase
import os


class TestCompareTranslatedSpecResults(EqualityTestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    @property
    def specifications(self):
        basepath = self.get_absolute_path('assets/languages')
        for filename in os.listdir(basepath):
            path = os.path.join(basepath, filename)
            yield path

    def test_spec_has_describes_editor_in_chief_role(self):
        failures = []

        for path in self.specifications:
            spec = self.get_spec(path)

            if 'Editor-In-Chief' not in spec.role_descriptions:
                failures.append(path)

        self.assertEquals(
            [], failures,
            'These language specs are not defining a role description for'
            ' the "Editor-In-Chief" role.')
