from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IPermissionCollector
from functools import reduce
from operator import itemgetter
from six.moves import map
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer


@implementer(IPermissionCollector)
class DefaultPermissionCollector(object):

    def collect(self, workflow_name):
        grouped = self.get_grouped_permissions(workflow_name)
        if not grouped:
            return []
        return sorted(set(reduce(list.__add__, list(grouped.values()))))

    def get_grouped_permissions(self, workflow_name, unmanaged=False):
        registry = getUtility(IActionGroupRegistry)
        result = {}

        for perm in self._get_permissions():
            action_groups = registry.get_action_groups_for_permission(
                perm, workflow_name=workflow_name)

            if unmanaged and not action_groups:
                action_groups = ['unmanaged']

            for action_group in action_groups:
                if action_group not in result:
                    result[action_group] = set()
                result[action_group].add(perm)

        for key, value in result.items():
            result[key] = sorted(value)

        return result

    def _get_permissions(self):
        site = getSite()
        return list(map(itemgetter(0), site.ac_inherited_permissions(1)))
