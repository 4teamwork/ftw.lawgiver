from collections import defaultdict
from ftw.lawgiver.interfaces import IActionGroupRegistry
from zope.interface import implements


class ActionGroupRegistry(object):

    implements(IActionGroupRegistry)

    def __init__(self):
        self._permissions = {}
        self._ignores = defaultdict(set)

    def update(self, action_group, permissions, workflow=None):
        for perm in permissions:
            if perm not in self._permissions:
                self._permissions[perm] = {}

            self._permissions[perm][workflow] = action_group

    def ignore(self, permissions, workflow=None):
        self._ignores[workflow].update(permissions)

    def get_action_groups_for_workflow(self, workflow_name):
        result = {}

        ignored_permissions = self.get_ignored_permissions(workflow_name)

        for permission, workflows in self._permissions.items():
            if permission in ignored_permissions:
                continue

            if workflow_name in workflows:
                wfname = workflow_name
            elif None in workflows:
                wfname = None
            else:
                continue

            group = workflows[wfname]
            if group not in result:
                result[group] = set()

            result[group].add(permission)

        return result

    def get_action_group_for_permission(self, permission_title,
                                        workflow_name=None):
        if permission_title not in self._permissions:
            return None

        if permission_title in self.get_ignored_permissions(workflow_name):
            return None

        permission = self._permissions[permission_title]
        return permission.get(workflow_name, permission.get(None, None))

    def get_ignored_permissions(self, workflow_name=None):
        globally_ignored_permissions = set(self._ignores[None])
        permissions_ignored_by_workflow = set(self._ignores[workflow_name])

        permissions_managed_by_workflow = set(
            [permission for permission, workflows in self._permissions.items()
             if workflow_name in workflows])

        permissions = (globally_ignored_permissions
                       - permissions_managed_by_workflow)
        permissions.update(permissions_ignored_by_workflow)
        return permissions
