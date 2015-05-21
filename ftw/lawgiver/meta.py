from AccessControl.security import PermissionDirective
from ftw.lawgiver.actiongroups import ActionGroupRegistry
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IDynamicRoleAdapter
from ftw.lawgiver.localroles import create_dynamic_role
from ftw.lawgiver.schema import CommaSeparatedText
from zope.component import provideUtility
from zope.component import queryUtility
from zope.configuration.exceptions import ConfigurationError
from zope.configuration.fields import MessageID
from zope.interface import Interface
from zope.schema import Bool
from zope.schema import TextLine
import zope.component.zcml


class IMapPermissionsDirective(Interface):

    action_group = MessageID(
        title=u'The name of the action group',
        description=u'',
        required=True)

    permissions = CommaSeparatedText(
        title=u'Permissions',
        description=u'A list of permissions',
        required=True)

    workflow = TextLine(
        title=u'The name of the workflow',
        description=u'By default the directive contents'
        u' apply to all workflows. Set the name of the'
        u' workflow here for making it workflow specific.',
        default=None,
        required=False)

    move = Bool(
        title=u'Move permissions from original to this action group',
        description=u'When True (default), the permissions are removed'
        u' from whether action groups they were mapped before.'
        u' By setting it to False, permissions can appear in multiple'
        u' action groups.',
        default=True,
        required=False)


class IIgnorePermissionsDirective(Interface):

    permissions = CommaSeparatedText(
        title=u'Permissions',
        description=u'A list of permissions',
        required=True)

    workflow = TextLine(
        title=u'The name of the workflow',
        description=u'By default the directive contents'
        u' apply to all workflows. Set the name of the'
        u' workflow here for making it workflow specific.',
        default=None,
        required=False)


class ISharingPageRoleDirective(Interface):

    name = TextLine(
        title=u'Role name',
        description=u'The name of the role.',
        required=True)

    permission = TextLine(
        title=u'Required permission',
        description=u'The required permission for delegating this role.',
        required=False)

    register_permission = Bool(
        title=u'Register required permission',
        description=u'Register the required permission in Zope.',
        required=False,
        default=True)

    map_permission = Bool(
        title=u'Map required permission for lawgiver',
        description=u'Map required permission to the default lawgiver action '
        u'gorup "manage security".',
        required=False,
        default=True)


def mapPermissions(_context, **kwargs):
    """Map permissions to an action group.
    """

    permissions = kwargs['permissions']
    for permission in permissions:
        if '   ' in permission:
            raise ConfigurationError(
                'Seems that a comma is missing in the "permissions"'
                ' attribute of the lawgiver:map_permissions tag.')

    if permissions[-1] == '':
        permissions.pop()

    component = queryUtility(IActionGroupRegistry)
    if component is None:
        component = ActionGroupRegistry()
        provideUtility(component)

    component.update(**kwargs)


def ignorePermissions(_context, **kwargs):
    """Ignore permissions for a workflow.
    """

    permissions = kwargs['permissions']
    for permission in permissions:
        if '   ' in permission:
            raise ConfigurationError(
                'Seems that a comma is missing in the "permissions"'
                ' attribute of the lawgiver:map_permissions tag.')

    if permissions[-1] == '':
        permissions.pop()

    component = queryUtility(IActionGroupRegistry)
    if component is None:
        component = ActionGroupRegistry()
        provideUtility(component)

    component.ignore(**kwargs)


def sharingPageRole(_context, name, permission=None,
                    register_permission=True, map_permission=True):
    """Register a role for display on the sharing page.
    """

    if permission is None:
        permission = 'Sharing page: Delegate %s role' % name

    role_utility_factory, role_adapter_factory = create_dynamic_role(
        name, permission)

    zope.component.zcml.utility(_context,
                                factory=role_utility_factory,
                                name=name)

    zope.component.zcml.adapter(_context,
                                provides=IDynamicRoleAdapter,
                                factory=[role_adapter_factory],
                                for_=(Interface, Interface),
                                name=name)

    if register_permission:
        permission_id = '.'.join((_context.context.package.__name__,
                                  'Delegate%s' % (name.replace(' ', ''))))
        PermissionDirective(_context,
                            id=permission_id,
                            title=permission).after()

    if map_permission:
        mapPermissions(_context,
                       permissions=[permission],
                       action_group='manage security')
