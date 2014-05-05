from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.publisher.browser import BrowserView
import os.path


class ListSpecifications(BrowserView):

    def specifications(self):
        discovery = getMultiAdapter((self.context, self.request),
                                    IWorkflowSpecificationDiscovery)

        specs = map(self._get_spec_item, discovery.discover())
        return sorted(specs, key=lambda spec: spec['link_text'])

    def _get_spec_item(self, path):
        discovery = getMultiAdapter((self.context, self.request),
                                    IWorkflowSpecificationDiscovery)

        workflow_name = os.path.basename(os.path.dirname(path))
        item = {'link_text': workflow_name,
                'description': '',
                'href': '/'.join((
                    self.context.absolute_url(),
                    '@@lawgiver-spec-details',
                    discovery.hash(path)))}

        specification = self._get_specification_by_path(path)
        if specification and specification.title:
            item['link_text'] = '%s (%s)' % (specification.title,
                                             workflow_name)

        if specification and specification.description:
            item['description'] = specification.description

        return item

    def _get_specification_by_path(self, path):
        """Returns the parsed specification for a path pointing to a
        specification.txt
        """
        parser = getUtility(IWorkflowSpecificationParser)

        with open(path) as specfile:
            return parser(specfile, path=path, silent=True)
