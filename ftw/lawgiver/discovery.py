from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.languages import LANGUAGES
from operator import itemgetter
from operator import methodcaller
from Products.CMFCore.utils import getToolByName
from zope.component import adapter
from zope.interface import implementer
from zope.interface import Interface
import hashlib
import os


@implementer(IWorkflowSpecificationDiscovery)
@adapter(Interface, Interface)
class WorkflowSpecificationDiscovery(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def discover(self):
        result = set()
        for item in map(self._get_specification_files, self._get_profile_paths()):
            result.update(item)
        return list(result)

    def hash(self, path):
        return hashlib.md5(path.encode('utf-8')).hexdigest()

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
