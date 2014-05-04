from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.languages import LANGUAGES
from operator import itemgetter
from operator import methodcaller
from zope.component import adapts
from zope.interface import Interface
from zope.interface import implements
import hashlib
import os


class WorkflowSpecificationDiscovery(object):
    implements(IWorkflowSpecificationDiscovery)
    adapts(Interface, Interface)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def discover(self):
        result = set()
        map(result.update,
            map(self._get_specification_files, self._get_profile_paths()))
        return list(result)

    def hash(self, path):
        return hashlib.md5(path).hexdigest()

    def unhash(self, hash_):
        for path in self.discover():
            if self.hash(path) == hash_:
                return path
        return None

    def _get_specification_files(self, profile_directory):
        workflows_dir = os.path.join(profile_directory, 'workflows')
        if not os.path.isdir(workflows_dir):
            return

        for name in os.listdir(workflows_dir):
            for language in LANGUAGES.values():
                specpath = os.path.join(workflows_dir, name, language.filename)
                if os.path.isfile(specpath):
                    yield specpath
                    break

    def _get_profile_paths(self):
        setup_tool = getToolByName(self.context, 'portal_setup')
        paths = map(itemgetter('path'), setup_tool.listProfileInfo())
        return map(str, filter(methodcaller('startswith', '/'), paths))
