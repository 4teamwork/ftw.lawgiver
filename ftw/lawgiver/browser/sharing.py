from Products.CMFCore.utils import getToolByName
from collections import defaultdict
from ftw.lawgiver import _
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from plone.app.workflow.interfaces import ISharingPageRole
from zope.component import getMultiAdapter
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.i18n import translate
from zope.publisher.browser import BrowserView
import os.path


class SharingDescribeRole(BrowserView):

    CHECKED = r'<span class="checked">&#x2713;</span>'
    NOT_CHECKED = r'<span class="not-checked"></span>'

    def available(self):
        """Returns True when sharing description is available for this
        context. It is only available when a lawgiver workflow is used
        for this context.
        """
        workflow = self.get_local_workflow()
        if not workflow:
            return False
        return bool(self.get_specification(workflow))

    def get_table_data(self):
        workflow = self.get_local_workflow()
        if not workflow:
            return None

        spec = self.get_specification(workflow)
        if not spec:
            return None

        rolename = self.get_untranslated_role_name(spec)
        if rolename is None:
            return None

        action_groups = defaultdict(dict)
        for status in spec.states.values():
            statements = filter(
                lambda role_to_group: role_to_group[0] == rolename,
                status.statements)

            for _role, action_group in statements:
                action_groups[action_group][status.title] = self.CHECKED

        headers = [_(u'sharing_description_action', u'Action')]
        generator = getUtility(IWorkflowGenerator)
        generator.workflow_id = workflow.id
        for status in spec.states.values():
            headers.append(self.translate(generator._status_id(status),
                                          default=status.title))

        action_group_rows = []
        transition_rows = []
        transitions = [transition.title for transition in spec.transitions]
        for action_group_title, states_map in action_groups.items():
            row = [self.translate(action_group_title)]
            for status in spec.states.keys():
                row.append(self.CHECKED if status in states_map
                           else self.NOT_CHECKED)
            if action_group_title in transitions:
                transition_rows.append(row)
            else:
                action_group_rows.append(row)

        action_group_rows.sort()
        transition_rows.sort()

        return {'headers': headers,
                'rows': action_group_rows + transition_rows}

    def get_untranslated_role_name(self, spec):
        translated_rolename = self.request.get('role', None)
        reversed_role_mapping = dict(zip(*reversed(
                    zip(*spec.role_mapping.items()))))

        for name, utility in getUtilitiesFor(ISharingPageRole):
            if self.translate(utility.title) != translated_rolename:
                continue

            if name in reversed_role_mapping:
                return reversed_role_mapping[name]

        return translated_rolename

    def get_action_groups(self, workflow_name):
        collector = getUtility(IPermissionCollector)
        managed = collector.get_grouped_permissions(workflow_name)
        return sorted(managed.keys())

    def get_specification(self, workflow):
        discovery = getMultiAdapter((self.context, self.request),
                            IWorkflowSpecificationDiscovery)
        parser = getUtility(IWorkflowSpecificationParser)

        for path in discovery.discover():
            if os.path.basename(os.path.dirname(path)) != workflow.id:
                continue

            with open(path) as specfile:
                return parser(specfile, path=path, silent=True)

        return None

    def get_local_workflow(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        workflows = wftool.getWorkflowsFor(self.context)
        if len(workflows) == 0:
            return None
        else:
            return workflows[0]

    def translate(self, msgid, default=None):
        plone = translate(
            msgid,
            context=self.request,
            domain='plone',
            default=default)

        lawgiver = translate(
            msgid,
            context=self.request,
            domain='ftw.lawgiver',
            default=plone)

        return lawgiver[0].upper() + lawgiver[1:]
