from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.interface import implements


class SpecificationParser(object):

    implements(IWorkflowSpecificationParser)

    def parse(self, stream):
        return None
