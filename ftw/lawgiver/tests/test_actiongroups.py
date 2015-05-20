from ftw.lawgiver.actiongroups import ActionGroupRegistry
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.testing import META_ZCML
from ftw.lawgiver.tests.base import BaseTest
from zope.component import getUtility
from zope.configuration.exceptions import ConfigurationError
from zope.interface.verify import verifyClass


class TestBundlesZCML(BaseTest):

    layer = META_ZCML

    def get_registry(self):
        return getUtility(IActionGroupRegistry)

    def test_directive_registers_and_updates_registry(self):
        self.load_map_permissions_zcml(
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
            self.load_map_permissions_zcml(
                '<lawgiver:map_permissions',
                '    permissions="Access contents information" />',
                )

    def test_permissions_required(self):
        with self.assertRaises(ConfigurationError):
            self.load_map_permissions_zcml(
                '<lawgiver:map_permissions',
                '    action_group="view" />',
                )


class TestIgnoreZCML(BaseTest):

    layer = META_ZCML

    def get_registry(self):
        return getUtility(IActionGroupRegistry)

    def test_directive_registers_and_updates_registry(self):
        self.load_map_permissions_zcml(
            '<lawgiver:ignore',
            '    permissions="Access contents information,'
            '                 View'
            '                " />',

            '<lawgiver:ignore',
            '    workflow="foo"',
            '    permissions="List folder contents" />',
            )

        registry = self.get_registry()
        self.assertEquals(
            {None: set([u'Access contents information', u'View']),
             u'foo': set([u'List folder contents'])},

            dict(registry._ignores))

    def test_permissions_required(self):
        with self.assertRaises(ConfigurationError):
            self.load_map_permissions_zcml(
                '<lawgiver:ignore',
                '    workflow="foo" />')

    def test_invalid_permission_syntax_detected(self):
        with self.assertRaises(ConfigurationError) as context_manager:
            self.load_map_permissions_zcml(
                '<lawgiver:ignore',
                '    permissions="Foo'
                '                 Bar" />')

        exception_message = str(context_manager.exception)
        self.assertIn('ConfigurationError: Seems that a comma is missing',
                      exception_message)


class TestActionGroupRegistry(BaseTest):

    layer = META_ZCML

    def get_registry(self):
        return getUtility(IActionGroupRegistry)

    def test_registry_implements_interface(self):
        self.assertTrue(
            IActionGroupRegistry.implementedBy(ActionGroupRegistry),
            'ActionGroupRegistry does not provide IActionGroupRegistry')

        verifyClass(IActionGroupRegistry, ActionGroupRegistry)

    def test_get_action_groups_for_workflow_GLOBAL(self):
        self.load_map_permissions_zcml(
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
        self.load_map_permissions_zcml(
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

    def test_get_action_groups_for_permission(self):
        self.load_map_permissions_zcml(
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
            ['view'],
            registry.get_action_groups_for_permission(
                'View'))

        self.assertEqual(
            ['edit'],
            registry.get_action_groups_for_permission(
                'Modify portal content'))

        self.assertEqual(
            [],
            registry.get_action_groups_for_permission(
                'Bar'))

        # with specifying a workflow
        self.assertEqual(
            ['view'],
            registry.get_action_groups_for_permission(
                'View', workflow_name='foo'))

        self.assertEqual(
            ['view'],
            registry.get_action_groups_for_permission(
                'Modify portal content', workflow_name='foo'))

        self.assertEqual(
            ['view'],
            registry.get_action_groups_for_permission(
                'Bar', workflow_name='foo'))

        self.assertEqual(
            [],
            registry.get_action_groups_for_permission(
                'A unregistered permission'))

    def test_detect_possible_missing_comma(self):
        with self.assertRaises(ConfigurationError) as cm:
            self.load_map_permissions_zcml(
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
        self.load_map_permissions_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information,',
            '                 View," />')

        registry = self.get_registry()

        self.assertEquals(
            sorted(['Access contents information', 'View']),
            sorted(registry._permissions.keys()),

            'Trailing comma seems not to be working in map_permissions ZCML.')

    def test_getting_ignored_permissions(self):
        self.load_map_permissions_zcml(
            '<lawgiver:ignore',
            '    permissions="Access contents information" />',
            )

        registry = self.get_registry()

        self.assertEqual(set([u'Access contents information']),
                         registry.get_ignored_permissions())

    def test_getting_ignored_permissions_for_a_workflow(self):
        self.load_map_permissions_zcml(
            '<lawgiver:ignore',
            '    permissions="Access contents information" />',

            '<lawgiver:ignore',
            '    workflow="foo"'
            '    permissions="View" />',
            )

        registry = self.get_registry()

        self.assertEqual(set([u'Access contents information', u'View']),
                         registry.get_ignored_permissions('foo'))

    def test_ignoring_permissions_removes_them_from_groups(self):
        self.load_map_permissions_zcml(
            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    permissions="Access contents information,'
            '                 List folder contents,'
            '                 View" />',

            '<lawgiver:ignore',
            '    permissions="Access contents information" />',

            '<lawgiver:ignore',
            '    workflow="my_workflow"'
            '    permissions="List folder contents" />',
            )

        registry = self.get_registry()

        self.assertEqual(
            {'view': set([u'View'])},
            registry.get_action_groups_for_workflow('my_workflow'))

        self.assertEqual(
            [],
            registry.get_action_groups_for_permission(
                'Access contents information'))

        self.assertEqual(
            [],
            registry.get_action_groups_for_permission(
                'List folder contents', workflow_name='my_workflow'))

        self.assertEqual(
            ['view'],
            registry.get_action_groups_for_permission(
                'List folder contents'))

    def test_remap_ignored_permissions_for_a_workflow(self):
        self.load_map_permissions_zcml(
            '<lawgiver:ignore',
            '    permissions="Access contents information" />',

            '<lawgiver:map_permissions',
            '    action_group="view"',
            '    workflow="my_workflow"',
            '    permissions="Access contents information" />',
            )

        registry = self.get_registry()

        self.assertEqual(
            {'group': [u'view'],
             'ignored': set([]),
             'view_permissions': set([u'Access contents information'])},

            {'group': registry.get_action_groups_for_permission(
                    'Access contents information', workflow_name='my_workflow'),
             'ignored': registry.get_ignored_permissions('my_workflow'),
             'view_permissions': (
                    registry.get_action_groups_for_workflow(
                        'my_workflow').get('view'))},

            'Remapping a globally ignored permission to an action group for a'
            ' specific workflow should make it be re-managed and in the right'
            ' action group for this workflow, but it does not.')

        self.assertEqual(
            {'group': [],
             'ignored': set([u'Access contents information']),
             'view_permissions': None},

            {'group': registry.get_action_groups_for_permission(
                    'Access contents information', workflow_name='default'),
             'ignored': registry.get_ignored_permissions('default'),
             'view_permissions': (
                    registry.get_action_groups_for_workflow('default').get('view'))},

            'Remapping a globally ignored permission to an action group for a'
            ' specific workflow should keep it ignored for other workflows')

    def test_map_permission_to_multiple_action_groups(self):
        self.load_map_permissions_zcml(
            '<lawgiver:ignore',
            '    permissions="Access contents information" />',

            '<lawgiver:map_permissions',
            '    action_group="add"',
            '    permissions="Add portal content,'
            '                 Add folder,'
            '                 Add ticket" />',

            '<lawgiver:map_permissions',
            '    action_group="add ticket"',
            '    permissions="Add ticket"'
            '    workflow="custom"'
            '    move="True" />',

            '<lawgiver:map_permissions',
            '    action_group="add ticket"',
            '    permissions="Add portal content"'
            '    workflow="custom"'
            '    move="False" />',
            )

        registry = self.get_registry()
        self.assertEquals(
            {u'add': set([u'Add folder', u'Add portal content']),
             u'add ticket': set([u'Add ticket', u'Add portal content'])},

            registry.get_action_groups_for_workflow('custom'))
