from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IPermissionCollector
from operator import itemgetter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implements


class DefaultPermissionCollector(object):
    implements(IPermissionCollector)

    def collect(self, workflow_name):
        grouped = self.get_grouped_permissions(workflow_name)
        if not grouped:
            return []
        return sorted(reduce(list.__add__, grouped.values()))

    def get_grouped_permissions(self, workflow_name, unmanaged=False):
        registry = getUtility(IActionGroupRegistry)
        result = {}

        for perm in self._get_permissions():
            action_group = registry.get_action_group_for_permission(
                perm, workflow_name=workflow_name)
            if action_group is None and not unmanaged:
                continue

            elif action_group is None:
                action_group = 'unmanaged'

            if action_group not in result:
                result[action_group] = set()

            result[action_group].add(perm)

        for key, value in result.items():
            result[key] = sorted(value)

        return result

    def _get_permissions(self):
        site = getSite()
        return map(itemgetter(0), site.ac_inherited_permissions(1))
