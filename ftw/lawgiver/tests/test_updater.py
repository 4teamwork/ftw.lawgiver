from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from unittest2 import TestCase
from zope.component import getUtility
import os.path


TESTS_DIRECTORY = os.path.dirname(__file__)

BAR_DEFINITION_XML = os.path.abspath(os.path.join(
        TESTS_DIRECTORY,
        'profiles', 'bar', 'workflows', 'wf-bar', 'definition.xml'))

BAR_SPECIFICATION = os.path.abspath(os.path.join(
        TESTS_DIRECTORY,
        'profiles', 'bar', 'workflows', 'wf-bar', 'specification.txt'))


class TestUpdater(TestCase):
    layer = SPECIFICATIONS_FUNCTIONAL

    def tearDown(self):
        if os.path.exists(BAR_DEFINITION_XML):
            os.remove(BAR_DEFINITION_XML)

    def test_write_workflow(self):
        updater = getUtility(IUpdater)
        self.assertFalse(os.path.exists(BAR_DEFINITION_XML),
                         'Expected that there is not yet a wf definition.')
        updater.write_workflow(BAR_SPECIFICATION)
        self.assertTrue(os.path.exists(BAR_DEFINITION_XML),
                        'Workflow definition was not generated.')

    def test_update_translations(self):
        updater = getUtility(IUpdater)
        updater.update_translations(BAR_SPECIFICATION)
