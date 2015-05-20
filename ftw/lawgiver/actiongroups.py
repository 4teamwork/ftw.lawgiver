from collections import defaultdict
from ftw.lawgiver.interfaces import IActionGroupRegistry
from zope.interface import implements


class ActionGroupRegistry(object):

    implements(IActionGroupRegistry)

    def __init__(self):
        self._permissions = {}
        self._extending_permissions = {}
        self._ignores = defaultdict(set)

    def update(self, action_group, permissions, workflow=None, move=True):
        if move:
            for permission in permissions:
                self._update_default_permission(
                    permission, workflow, action_group)
        else:
            for permission in permissions:
                self._update_extending_permissions(
                    permission, workflow, action_group)

    def ignore(self, permissions, workflow=None):
        self._ignores[workflow].update(permissions)

    def get_action_groups_for_workflow(self, workflow_name):
        result = {}

        ignored_permissions = self.get_ignored_permissions(workflow_name)

        for permission, workflows in self._merged_permissions().items():
            if permission in ignored_permissions:
                continue

            if workflow_name in workflows:
                wfname = workflow_name
            elif None in workflows:
                wfname = None
            else:
                continue

            for group in workflows[wfname]:
                if group not in result:
                    result[group] = set()
                result[group].add(permission)

        return result

    def get_action_groups_for_permission(self, permission_title,
                                         workflow_name=None):
        if permission_title not in self._merged_permissions():
            return []

        if permission_title in self.get_ignored_permissions(workflow_name):
            return []

        permission = self._merged_permissions()[permission_title]
        return permission.get(workflow_name, permission.get(None, []))

    def get_ignored_permissions(self, workflow_name=None):
        globally_ignored_permissions = set(self._ignores[None])
        permissions_ignored_by_workflow = set(self._ignores[workflow_name])

        permissions_managed_by_workflow = set(
            [permission for permission, workflows
             in self._merged_permissions().items()
             if workflow_name in workflows])

        permissions = (globally_ignored_permissions
                       - permissions_managed_by_workflow)
        permissions.update(permissions_ignored_by_workflow)
        return permissions

    def _update_default_permission(self, permission, workflow, action_group):
        if permission not in self._permissions:
            self._permissions[permission] = {}

        self._permissions[permission][workflow] = action_group

    def _update_extending_permissions(self, permission, workflow,
                                      action_group):
        if permission not in self._extending_permissions:
            self._extending_permissions[permission] = {}

        if workflow in self._extending_permissions[permission]:
            self._extending_permissions[permission][workflow].append(
                action_group)
        else:
            self._extending_permissions[permission][workflow] = [action_group]

    def _merged_permissions(self):
        result = {}
        for permission in set(self._permissions.keys() +
                              self._extending_permissions.keys()):
            result[permission] = (
                self._merged_action_groups_mapping_for_perm(permission))

        return result

    def _merged_action_groups_mapping_for_perm(self, permission):
        workflows = set(self._permissions.get(permission, {}).keys() +
                        self._extending_permissions.get(permission, {}).keys())
        result = {}
        for workflow in workflows:
            result[workflow] = self._merged_action_groups_for_perm_in_wf(
                permission, workflow)
        return result

    def _merged_action_groups_for_perm_in_wf(self, permission, workflow):
        result = []

        default_perm_info = self._permissions.get(permission, {})
        if workflow in default_perm_info:
            result.append(default_perm_info[workflow])
        elif None in default_perm_info:
            result.append(default_perm_info[None])

        extending_perm_info = self._extending_permissions.get(permission, {})
        if workflow in extending_perm_info:
            result.extend(extending_perm_info[workflow])
        elif None in extending_perm_info:
            result.extend(extending_perm_info[None])

        return result
