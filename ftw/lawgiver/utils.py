from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
import os.path


def get_workflow_for(context):
    wftool = getToolByName(getSite(), 'portal_workflow')

    while context and not IContentish.providedBy(context):
        context = aq_parent(aq_inner(context))
    if not context:
        return None

    workflows = wftool.getWorkflowsFor(context)
    if len(workflows) == 0:
        return None
    else:
        return workflows[0]


def get_specification(workflow_id):
    discovery = getMultiAdapter((getSite(), getSite().REQUEST),
                        IWorkflowSpecificationDiscovery)
    parser = getUtility(IWorkflowSpecificationParser)

    for path in discovery.discover():
        if os.path.basename(os.path.dirname(path)) != workflow_id:
            continue

        with open(path) as specfile:
            return parser(specfile, path=path, silent=True)

    return None


def get_specification_for(context):
    workflow = get_workflow_for(context)
    if not workflow:
        return None

    return get_specification(workflow.id)
