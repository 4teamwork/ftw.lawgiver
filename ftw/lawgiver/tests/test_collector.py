from ftw.lawgiver.collector import DefaultPermissionCollector
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.testing import META_ZCML
from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.tests.base import BaseTest
from ftw.testing import MockTestCase
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface.verify import verifyObject


class TestComponentRegistered(MockTestCase):

    layer = ZCML_FIXTURE

    def test_component_registered(self):
        self.assertTrue(
            queryUtility(IPermissionCollector, name=''),
            'The default IPermissionCollector utility (name="") is'
            ' not registered properly.')

    def test_implements_interface(self):
        comp = getUtility(IPermissionCollector, name='')
        self.assertTrue(IPermissionCollector.providedBy(comp))
        verifyObject(IPermissionCollector, comp)


class TestDefaultPermissionCollector(BaseTest):

    layer = META_ZCML

    def setUp(self):
        super(TestDefaultPermissionCollector, self).setUp()
        import zope.security
        self.layer.load_zcml_file('meta.zcml', zope.security)

    @property
    def collector(self):
        return DefaultPermissionCollector()

    def test_collect_permissions_DEFAULT(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(set(['Add portal content', 'View']),
                          set(self.collector.collect('foo')))

    def test_collect_permissions_NON_DEFAULT(self):
        self.register_permissions(**{'zope2.View': 'View'})
        self.map_permissions(['View'], 'view', workflow_name='foo')

        self.assertEquals([], self.collector.collect('bar'))

    def test_collect_permissions_MIXED(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view', workflow_name='foo')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(['Add portal content'],
                          self.collector.collect('bar'))

    def test_collect_permissions_UNREGISTERED(self):
        self.register_permissions(**{'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(['View'],
                          self.collector.collect('bar'))

    def test_is_permission_registered__YES(self):
        self.register_permissions(**{
                'cmf.ListFolderContents': 'List folder contents'})

        self.assertTrue(self.collector.is_permission_registered(
                'List folder contents'))

    def test_is_permission_registered__NO(self):
        self.assertFalse(self.collector.is_permission_registered(
                'List folder contents'))