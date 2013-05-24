from ftw.lawgiver.actiongroups import ActionGroupRegistry
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.schema import CommaSeparatedText
from zope.component import provideUtility
from zope.component import queryUtility
from zope.configuration.exceptions import ConfigurationError
from zope.interface import Interface
from zope.schema import TextLine


class IMapPermissionsDirective(Interface):

    action_group = TextLine(
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
