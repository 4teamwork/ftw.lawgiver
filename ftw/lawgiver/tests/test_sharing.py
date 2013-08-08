from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.pages import Sharing
from plone.app.testing import TEST_USER_ID
from plone.app.testing import setRoles
from unittest2 import TestCase


class TestSharingRoleTranslation(TestCase):

    layer = SPECIFICATIONS_FUNCTIONAL

    def setUp(self):
        portal = self.layer['portal']
        setRoles(portal, TEST_USER_ID, ['Manager'])

    def test_default_role_translation_for_default_workflows(self):
        page = create(Builder('page'))

        Sharing().login().visit_on(page)

        self.assertEquals(
            ['Can add', 'Can edit', 'Can review', 'Can view'],
            Sharing().role_labels)
