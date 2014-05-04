from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import EqualityTestCase


class TestCompareTranslatedSpecResults(EqualityTestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    specifications = ['assets/languages/specification.txt',
                      'assets/languages/specification.de.txt']
