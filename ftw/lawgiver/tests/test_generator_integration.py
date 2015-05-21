from StringIO import StringIO
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.tests.base import BaseTest
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getUtility
from zope.component import provideUtility
from zope.component import queryUtility
from zope.interface.verify import verifyObject
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

        import plone.i18n.normalizer
        provideUtility(plone.i18n.normalizer.idnormalizer,
                       plone.i18n.normalizer.IIDNormalizer)

        # use an empty permission mapping registry
        registry = getUtility(IActionGroupRegistry)
        self._ori_permissions = registry._permissions
        registry._permissions = {}

        self.register_permissions(**{
                'cmf.ModifyPortalContent': 'Modify portal content',
                'zope2.View': 'View',
                'zope2.AccessContentsInformation': \
                    'Access contents information',
                'zope2.DeleteObjects': 'Delete objects',
                'cmf.AddPortalContent': 'Add portal content',
                'cmf.AccessFuturePortalContent': \
                    'Access future portal content',
                'ATContentTypes: Add Image': 'ATContentTypes: Add Image',
                })

        self.map_permissions(['View', 'Access contents information'], 'view')
        self.map_permissions(['Modify portal content'], 'edit')
        self.map_permissions(['Delete objects'], 'delete')
        self.map_permissions(['Add portal content',
                              'ATContentTypes: Add Image'],
                             'add')
        self.map_permissions(['Add portal content', 'ATContentTypes: Add Folder'],
                             'add folder', move=False)
        self.map_permissions(['Access future portal content'], 'view future')
        self.map_permissions(['ATContentTypes: Add Image'], 'edit',
                             workflow_name='my_custom_workflow')

    def tearDown(self):
        registry = getUtility(IActionGroupRegistry)
        registry._permissions = self._ori_permissions
        super(TestGeneratorIntegration, self).tearDown()

    def test_component_registered(self):
        self.assertTrue(queryUtility(IWorkflowGenerator),
                        'The IWorkflowGenerator utility is not registered.')

    def test_component_implements_interface(self):
        component = getUtility(IWorkflowGenerator)
        self.assertTrue(IWorkflowGenerator.providedBy(component))

        verifyObject(IWorkflowGenerator, component)

    def test_generate_xml(self):
        parser = getUtility(IWorkflowSpecificationParser)

        spec_path = os.path.join(ASSETS, 'example.specification.txt')
        with open(spec_path) as spec_file:
            spec = parser(spec_file, path=spec_path)

        result = StringIO()
        generator = getUtility(IWorkflowGenerator)
        generator('my_custom_workflow', spec).write(result)

        expected_path = os.path.join(ASSETS, 'example.definition.xml')
        with open(expected_path) as expected_file:
            self.assert_definition_xmls(
                expected_file.read(), result.getvalue())
