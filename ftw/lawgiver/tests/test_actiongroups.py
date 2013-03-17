from ftw.lawgiver.actiongroups import ActionGroupRegistry
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import META_ZCML
from ftw.testing import MockTestCase
from zope.component import getUtility
from zope.configuration.exceptions import ConfigurationError
from zope.interface.verify import verifyClass


CONFIGURE = '''
<configure xmlns:lawgiver="http://namespaces.zope.org/lawgiver">
%s
</configure>
'''


class BaseTest(MockTestCase):

    layer = META_ZCML

    def load_zcml(self, *lines):
        zcml = CONFIGURE % '\n'.join(lines)
        self.layer.load_zcml_string(zcml)

    def get_registry(self):
        return getUtility(IActionGroupRegistry)


class TestBundlesZCML(BaseTest):

    def test_directive_registers_and_updates_registry(self):
        self.load_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="View" />',
            )

        registry = self.get_registry()
        self.assertEquals(set(registry._permissions.keys()),
                          set(['Access contents information',
                               'View']))

    def test_action_group_required(self):
        with self.assertRaises(ConfigurationError):
            self.load_zcml(
                '<lawgiver:map_permissions',
                '    permissions="Access contents information" />',
                )

    def test_permissions_required(self):
        with self.assertRaises(ConfigurationError):
            self.load_zcml(
                '<lawgiver:map_permissions',
                '    action_group="view" />',
                )


class TestActionGroupRegistry(BaseTest):

    def test_registry_implements_interface(self):
        self.assertTrue(
            IActionGroupRegistry.implementedBy(ActionGroupRegistry),
            'ActionGroupRegistry does not provide IActionGroupRegistry')

        verifyClass(IActionGroupRegistry, ActionGroupRegistry)

    def test_get_action_groups_for_workflow_GLOBAL(self):
        self.load_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="View" />',

            '<lawgiver:map_permissions',
            '    action_group="edit"',
            '    permissions="Modify portal content" />',
            )

        registry = self.get_registry()

        self.assertEqual(
            registry.get_action_groups_for_workflow('my_workflow'),

            {'view': set([u'Access contents information',
                          u'View']),

             'edit': set([u'Modify portal content'])})

    def test_get_action_groups_for_workflow_SPECIFIC_OVERRIDE(self):
        self.load_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information,',
            '                 View" />',

            '<lawgiver:map_permissions',
            '    action_group="edit"',
            '    permissions="Modify portal content" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Modify portal content"'
            '    workflow="foo" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="A custom permission for foo"'
            '    workflow="foo" />',
            )

        # we first register the modify permission under "edit"
        # and then register it also under "view" for "foo" only..

        registry = self.get_registry()

        self.assertEqual(
            registry.get_action_groups_for_workflow('my_workflow'),

            {'view': set([u'Access contents information',
                          u'View']),

             'edit': set([u'Modify portal content'])})

        self.assertEqual(
            registry.get_action_groups_for_workflow('foo'),

            {'view': set([u'Access contents information',
                          u'View',
                          u'Modify portal content',
                          u'A custom permission for foo'])})

    def test_get_action_group_for_permission(self):
        self.load_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="View" />',

            '<lawgiver:map_permissions',
            '    action_group="edit"',
            '    permissions="Modify portal content" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Modify portal content"'
            '    workflow="foo" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Bar"'
            '    workflow="foo" />',
            )

        registry = self.get_registry()

        # without specifying workflow
        self.assertEqual(
            'view',
            registry.get_action_group_for_permission(
                'View'))

        self.assertEqual(
            'edit',
            registry.get_action_group_for_permission(
                'Modify portal content'))

        self.assertEqual(
            None,
            registry.get_action_group_for_permission(
                'Bar'))

        # with specifying a workflow
        self.assertEqual(
            'view',
            registry.get_action_group_for_permission(
                'View', workflow_name='foo'))

        self.assertEqual(
            'view',
            registry.get_action_group_for_permission(
                'Modify portal content', workflow_name='foo'))

        self.assertEqual(
            'view',
            registry.get_action_group_for_permission(
                'Bar', workflow_name='foo'))

        self.assertEqual(
            None,
            registry.get_action_group_for_permission(
                'A unregistered permission'))

    def test_detect_possible_missing_comma(self):
        with self.assertRaises(ConfigurationError) as cm:
            self.load_zcml(
                '<lawgiver:map_permissions',
                '    action_group="view"',
                '    permissions="Access contents information',
                '                 View" />')

        self.assertEqual(
            'File "<string>", line 3.0-6.25\n    ConfigurationError:'
            ' Seems that a comma is missing in the "permissions" attribute'
            ' of the lawgiver:map_permissions tag.',
            str(cm.exception))

    def test_trailing_comma_works(self):
        self.load_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information,',
            '                 View," />')

        registry = self.get_registry()

        self.assertEquals(
            sorted(['Access contents information', 'View']),
            sorted(registry._permissions.keys()),

            'Trailing comma seems not to be working in map_permissions ZCML.')
