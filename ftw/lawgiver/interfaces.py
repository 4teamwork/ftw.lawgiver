# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument


from zope.interface import Interface


class IActionGroupRegistry(Interface):
    """An action group registry is an utility which knows all the action
    groups and which permissions are mapped to which action group.
    """

    def update(action_group, permissions, workflow=None):
        """Registers new `permissions` (each a string) to a `action_group`,
        optional only for a specific `workflow`.
        """

    def get_action_groups_for_workflow(workflow_name):
        """Returns a action groups to permissions mapping for a specific
        workflow (by `workflow_name`).

        The result is a dict where the key is the action group name and
        the value is a list of permissions (string).
        """

    def get_action_group_for_permission(permission_title, workflow_name=None):
        """Returns the name of the action group a permission is mapped to.
        Optional the `workflow_name` can be passed to make the query workflow
        specific.
        If the permission is not mapped, None is returned.
        """
