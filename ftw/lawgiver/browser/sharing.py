from collections import defaultdict
from ftw.lawgiver import _
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.utils import get_roles_inherited_by
from ftw.lawgiver.utils import get_specification_for
from ftw.lawgiver.utils import get_workflow_for
from ftw.lawgiver.utils import merge_role_inheritance
from plone.app.workflow.interfaces import ISharingPageRole
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.i18n import translate
from zope.publisher.browser import BrowserView


class SharingDescribeRole(BrowserView):

    CHECKED = r'<span class="checked">&#x2713;</span>'
    NOT_CHECKED = r'<span class="not-checked"></span>'

    def is_available(self):
        """Returns True when sharing description is available for this
        context. It is only available when a lawgiver workflow is used
        for this context.
        """
        return bool(get_specification_for(self.context))

    def __call__(self):
        self.table_data = None
        self.role_description = ''
        self._update()
        return super(SharingDescribeRole, self).__call__()

    def _update(self):
        spec = get_specification_for(self.context)
        workflow = get_workflow_for(self.context)
        if spec is None or workflow is None:
            return

        rolename = self._get_untranslated_role_name(spec)
        if rolename is None:
            return

        self.table_data = self._get_table_data(spec, workflow, rolename)
        self.role_description = self._get_role_description(
            spec, workflow, rolename)

    def _get_table_data(self, spec, workflow, rolename):
        return {'headers': self._generate_table_headers(spec, workflow),
                'rows': self._generate_table_rows(spec, rolename)}

    def _get_role_description(self, spec, workflow, rolename):
        default_description = None
        for role, description in spec.role_descriptions.items():
            if role.lower() == rolename.lower():
                default_description = description
                break

        if default_description is None:
            return ''

        plonerole = spec.role_mapping[rolename]
        generator = getUtility(IWorkflowGenerator)
        generator.workflow_id = workflow.id
        msgid = generator._role_description_id(plonerole)
        return self._translate(msgid, default=default_description)

    def _generate_table_headers(self, spec, workflow):
        """Generates and returns the table headers as list
        of cell values (string).
        """
        headers = [_(u'sharing_description_action', u'Action')]
        generator = getUtility(IWorkflowGenerator)
        generator.workflow_id = workflow.id
        for status in spec.states.values():
            headers.append(self._translate(generator._status_id(status),
                                           default=status.title))
        return headers

    def _generate_table_rows(self, spec, rolename):
        """Generates and returns a list of lists, each inner list
        representing a table row and containing the cell values as strings.
        """
        action_groups = self._get_action_group_grid_data(spec, rolename)

        action_group_rows = []
        transition_rows = []

        transitions = [transition.title for transition in spec.transitions]
        for action_group_title, states_map in action_groups.items():
            row = [self._translate(action_group_title)]

            for status in spec.states.keys():
                row.append(self.CHECKED if status in states_map
                           else self.NOT_CHECKED)

            if action_group_title in transitions:
                transition_rows.append(row)
            else:
                action_group_rows.append(row)

        action_group_rows.sort()
        transition_rows.sort()
        return action_group_rows + transition_rows

    def _get_action_group_grid_data(self, spec, rolename):
        """Returns a nested dict with the table / grid data, where
        the outer dict keys are the action groups and the innner
        dict keys are the statues and the inner dict values is the
        HTML cell value (tick character).

        result['edit']['Private'] = self.CHECKED
        """

        action_groups = defaultdict(dict)
        for status in spec.states.values():
            ploneroles = [spec.role_mapping[rolename]]

            role_inheritance = merge_role_inheritance(spec, status)
            ploneroles = get_roles_inherited_by(ploneroles, role_inheritance)
            statements = spec.generals + status.statements

            for statement_spec_role, action_group in statements:
                statement_plone_role = spec.role_mapping[statement_spec_role]
                if statement_plone_role not in ploneroles:
                    continue

                action_groups[action_group][status.title] = self.CHECKED

        return action_groups

    def _get_untranslated_role_name(self, spec):
        """From the AJAX request we have only the role-text which is used
        as table heading in @@sharing.
        This text is usually translated, but we need to know the actual
        Plone role.
        Therefore we need to find it by translating the Plone roles
        and compare it to the text.
        """

        translated_rolename = self.request.get('role', None)
        if translated_rolename is None:
            return None

        reversed_role_mapping = dict(zip(*reversed(
                    zip(*spec.role_mapping.items()))))

        for name, utility in getUtilitiesFor(ISharingPageRole):
            utility_rolename = translate(utility.title, context=self.request)
            if utility_rolename != translated_rolename:
                continue

            if name in reversed_role_mapping:
                return reversed_role_mapping[name]

        return None

    def _translate(self, msgid, default=None):
        if isinstance(msgid, str):
            msgid = msgid.decode('utf-8')

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
