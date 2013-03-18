from StringIO import StringIO
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.tests.base import BaseTest
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getUtility
import os


ASSETS = os.path.join(os.path.dirname(__file__), 'assets')


class TestGeneratorIntegration(BaseTest):
    """This test registers some necessary permissions and builds the
    assets/example.specification.txt end-to-end with parsing the spec
    and generating the XML.
    """

    layer = ZCML_FIXTURE

    def setUp(self):
        super(TestGeneratorIntegration, self).setUp()

        self.register_permissions(**{
                'cmf.ModifyPortalContent': 'Modify portal content',
                'zope2.View': 'View',
                'zope2.AccessContentsInformation': \
                    'Access contents information',
                'zope2.DeleteObjects': 'Delete objects',
                'cmf.AddPortalContent': 'Add portal content',
                'cmf.AccessFuturePortalContent': \
                    'Access future portal content',
                })

        self.map_permissions(['View', 'Access contents information'], 'view')
        self.map_permissions(['Modify portal content'], 'edit')
        self.map_permissions(['Delete objects'], 'delete')
        self.map_permissions(['Add portal content'], 'add')
        self.map_permissions(['Access future portal content'], 'view future')

    def test_generate_xml(self):
        parser = getUtility(IWorkflowSpecificationParser)

        spec_path = os.path.join(ASSETS, 'example.specification.txt')
        with open(spec_path) as spec_file:
            spec = parser(spec_file)

        result = StringIO()
        generator = getUtility(IWorkflowGenerator)
        generator('my_custom_workflow', spec, result)

        expected_path = os.path.join(ASSETS, 'example.definition.xml')
        with open(expected_path) as expected_file:
            self.assert_definition_xmls(
                expected_file.read(), result.getvalue())
