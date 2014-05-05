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
