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

    @property
    def collector(self):
        return DefaultPermissionCollector()

    def test_get_grouped_permissions_DEFAULT(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals({'edit': ['Add portal content'],
                           'view': ['View']},
                          self.collector.get_grouped_permissions('foo'))

    def test_get_grouped_permissions_NON_DEFAULT(self):
        self.register_permissions(**{'zope2.View': 'View'})
        self.map_permissions(['View'], 'view', workflow_name='foo')

        self.assertEquals({}, self.collector.get_grouped_permissions('bar'))

    def test_get_grouped_permissions_MIXED(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view', workflow_name='foo')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(
            {'edit': ['Add portal content']},
            self.collector.get_grouped_permissions('bar'))

    def test_get_grouped_permissions_UNREGISTERED(self):
        self.register_permissions(**{'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals({'view': ['View']},
                          self.collector.get_grouped_permissions('bar'))

    def test_get_grouped_permissions_UNMANAGED(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View',
                'cmf.ManageProperties': 'Manage properties'})

        self.map_permissions(['View'], 'view', workflow_name='foo')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(
            {'edit': ['Add portal content'],
             'unmanaged': ['Manage properties', 'View']},
            self.collector.get_grouped_permissions('bar', unmanaged=True))

        self.assertEquals(
            {'edit': ['Add portal content'],
             'view': ['View'],
             'unmanaged': ['Manage properties']},
            self.collector.get_grouped_permissions('foo', unmanaged=True))

    def test_collect_DEFAULT(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(['Add portal content', 'View'],
                          self.collector.collect('foo'))

    def test_collect_NON_DEFAULT(self):
        self.register_permissions(**{'zope2.View': 'View'})
        self.map_permissions(['View'], 'view', workflow_name='foo')

        self.assertEquals([], self.collector.collect('bar'))

    def test_collect_MIXED(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content',
                'zope2.View': 'View'})

        self.map_permissions(['View'], 'view', workflow_name='foo')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(
            ['Add portal content'],
            self.collector.collect('bar'))

    def test_collect_UNREGISTERED(self):
        self.register_permissions(**{'zope2.View': 'View'})

        self.map_permissions(['View'], 'view')
        self.map_permissions(['Add portal content'], 'edit')

        self.assertEquals(['View'],
                          self.collector.collect('bar'))

    def test_get_grouped_permissions_IN_MULTIPLE_GROUPS(self):
        self.register_permissions(**{
                'cmf.AddPortalContent': 'Add portal content'})

        self.map_permissions(['Add portal content'], 'add')
        self.map_permissions(['Add portal content'], 'edit', move=False)

        self.assertEquals({'add': ['Add portal content'],
                           'edit': ['Add portal content']},
                          self.collector.get_grouped_permissions('foo'))

        self.assertEquals(['Add portal content'],
                          self.collector.collect('foo'))
