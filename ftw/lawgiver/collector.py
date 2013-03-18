from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IPermissionCollector
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.interface import implements
from zope.security.interfaces import IPermission


class DefaultPermissionCollector(object):
    implements(IPermissionCollector)

    def collect(self, workflow_name):
        registry = getUtility(IActionGroupRegistry)
        action_groups = registry.get_action_groups_for_workflow(workflow_name)
        if not action_groups:
            return []

        return filter(self.is_permission_registered,
                      reduce(list.__add__,
                             map(list, action_groups.values())))

    def is_permission_registered(self, permission_title):
        for _id, component in getUtilitiesFor(IPermission):
            if component.title == permission_title:
                return True
        return False
