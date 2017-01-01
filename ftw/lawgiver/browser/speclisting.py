from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.updater import StatusMessageFormatter
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.publisher.browser import BrowserView
import os.path


class ListSpecifications(BrowserView):

    def __call__(self):
        if 'update_all_specifications' in self.request.form:
            updater = getUtility(IUpdater)
            updater.update_all_specifications(
                output_formatter=StatusMessageFormatter(self.request))

        if 'update_all_specifications_with_upgradestep' in self.request.form:
            updater = getUtility(IUpdater)
            updater.update_all_specifications_with_upgrade_step(
                output_formatter=StatusMessageFormatter(self.request))

        return super(ListSpecifications, self).__call__()

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
