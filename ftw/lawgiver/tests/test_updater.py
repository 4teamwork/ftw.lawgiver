from ftw.builder import Builder
from ftw.builder import create
from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.testing import LAWGIVER_FUNCTIONAL_TESTING
from ftw.lawgiver.testing import SPECIFICATIONS_FUNCTIONAL
from ftw.lawgiver.tests.base import XMLDiffTestCase
from path import Path
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

ASSETS = Path(__file__).joinpath('..', 'assets').abspath()


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


class TestUpdateSpecifications(XMLDiffTestCase):
    layer = LAWGIVER_FUNCTIONAL_TESTING

    def test_update_all_specifications(self):
        self.maxDiff = None

        package = create(Builder('package with workflow').with_layer(self.layer))
        workflow_dir = package.package_path.joinpath(
            'profiles', 'default', 'workflows', 'my_custom_workflow')
        wf_definition = workflow_dir.joinpath('definition.xml')
        wf_spec = workflow_dir.joinpath('specification.txt')

        with package.zcml_loaded(self.layer['configurationContext']):
            self.assertIn('A three state publication workflow',
                          wf_definition.bytes())

            wf_spec.write_bytes(wf_spec.bytes().replace(
                'Description: A three state publication workflow',
                'Description: Another three state publication workflow'))

            getUtility(IUpdater).update_all_specifications()
            self.assertNotIn('A three state publication workflow',
                             wf_definition.bytes())
            self.assertIn('Another three state publication workflow',
                          wf_definition.bytes())
