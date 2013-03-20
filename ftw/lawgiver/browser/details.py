from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.interface import implementer
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import IPublishTraverse
from zope.security.interfaces import IPermission
import os.path


@implementer(IPublishTraverse)
class SpecDetails(BrowserView):

    def __init__(self, context, request):
        super(SpecDetails, self).__init__(context, request)
        self._spec_hash = None

    def publishTraverse(self, request, name):
        # stop traversing, we have arrived
        request['TraversalRequestNameStack'] = []

        self._spec_hash = name
        return self

    def specification(self):
        parser = getUtility(IWorkflowSpecificationParser)
        path = self._get_spec_path()

        with open(path) as specfile:
            # handle errors
            return parser(specfile, silent=True)

    def workflow_name(self):
        path = self._get_spec_path()
        return os.path.basename(os.path.dirname(path))

    def raw_specification(self):
        path = self._get_spec_path()
        with open(path) as specfile:
            # handle errors
            return specfile.read()

    def _get_spec_path(self):
        discovery = getMultiAdapter((self.context, self.request),
                                    IWorkflowSpecificationDiscovery)

        assert self._spec_hash, \
            'Spec hash was not set in traversal: "%s"' % str(self._spec_hash)

        path = discovery.unhash(self._spec_hash)
        if path is None:
            raise ValueError(
                'Could not find any specification with hash "%s"' % str(
                    self._spec_hash))

        return path

    def get_permissions(self):
        managed = {}
        unmanaged = []
        workflow_name = self.workflow_name()

        registry = getUtility(IActionGroupRegistry)
        for _name, permission in getUtilitiesFor(IPermission):
            if ',' in permission.title:
                # permissions with commas in the title are not supported
                # because it conflicts with the comma separated ZCML.
                # e.g. "Public, everyone can access"
                continue

            group = registry.get_action_group_for_permission(
                permission.title, workflow_name=workflow_name)

            if not group:
                unmanaged.append(permission.title)

            else:
                if group not in managed:
                    managed[group] = []
                managed[group].append(permission.title)

        return {'managed': managed,
                'unmanaged': unmanaged}
