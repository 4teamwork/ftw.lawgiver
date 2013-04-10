from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import EqualityTestCase


class TestRoleInheritance(EqualityTestCase):

    layer = LAWGIVER_INTEGRATION_TESTING

    specifications = ['assets/equality.role-inheritance.one.txt',
                      'assets/equality.role-inheritance.two.txt']
