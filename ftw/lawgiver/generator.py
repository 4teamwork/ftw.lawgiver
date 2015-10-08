from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.utils import generate_role_translation_id
from ftw.lawgiver.utils import get_roles_inheriting_from
from ftw.lawgiver.utils import merge_role_inheritance
from ftw.lawgiver.variables import VARIABLES
from lxml import etree
from lxml import html
from plone.app.workflow.interfaces import ISharingPageRole
from plone.i18n.normalizer.interfaces import INormalizer
from zope.component import getUtilitiesFor
from zope.component import getUtility
from zope.i18n import translate
from zope.interface import implements


class WorkflowGenerator(object):

    implements(IWorkflowGenerator)

    def __init__(self):
        self.workflow_id = None
        self.specification = None
        self.managed_permissions = None
        self.document = None

    def __call__(self, workflow_id, specification):
        self.workflow_id = workflow_id
        self.specification = specification
        self.ignored_delegate_permissions = \
            self._get_ignored_delegate_permissions(specification)

        self.managed_permissions = sorted(
            getUtility(IPermissionCollector).collect(workflow_id))

        doc = self._create_document()
        self.document = doc

        status_nodes = {}
        for status in sorted(specification.states.values(),
                             key=lambda status: status.title):
            status_nodes[status] = self._add_status(doc, status)

        transition_nodes = {}
        for transition in sorted(specification.transitions,
                                 key=lambda transition: transition.title):
            transition_nodes[transition] = self._add_transition(
                doc, transition)

        self._apply_specification_statements(status_nodes, transition_nodes)

        self._add_variables(doc)
        return self

    def write(self, result_stream):
        if self.document is None:
            raise RuntimeError(
                'The specification was not yet generated.'
                ' Call the generator first.')

        etree.ElementTree(self.document).write(result_stream,
                                               pretty_print=True,
                                               xml_declaration=True,
                                               encoding='utf-8')

    def get_translations(self, workflow_id, specification):
        self.workflow_id = workflow_id

        result = {}

        for status in specification.states.values():
            result[status.title] = status.title

        for transition in specification.transitions:
            result[transition.title] = transition.title

        for customerrole, plonerole in specification.role_mapping.items():
            result[self._role_id(plonerole)] = getattr(
                customerrole, 'original', customerrole)

        for customerrole, description in \
                specification.role_descriptions.items():
            plonerole = specification.role_mapping[customerrole.lower()]
            result[self._role_description_id(plonerole)] = description

        self.workflow_id = None
        return result

    def get_states(self, workflow_id, specification):
        self.workflow_id = workflow_id
        result = []

        for status in specification.states.values():
            result.append(self._status_id(status))

        return result

    def _get_ignored_delegate_permissions(self, specification):
        if specification.visible_roles is None:
            # No limitations defined, show all roles.
            return []

        ignored_permissions = []
        roles_to_list = map(specification.role_mapping.get,
                            specification.visible_roles)

        for role_name, utility in getUtilitiesFor(ISharingPageRole):
            if role_name not in roles_to_list:
                ignored_permissions.append(utility.required_permission)

        return ignored_permissions

    def _create_document(self):
        root = etree.Element("dc-workflow")
        root.set('workflow_id', self.workflow_id)
        root.set('title', self.specification.title.decode('utf-8'))
        root.set('description', self.specification.description and
                 self.specification.description.decode('utf-8') or '')

        root.set('initial_state', self._status_id(
                self.specification.get_initial_status()))

        root.set('state_variable', 'review_state')
        root.set('manager_bypass', 'True')

        for permission in self.managed_permissions:
            etree.SubElement(root, 'permission').text = permission.decode(
                'utf-8')

        return root

    def _add_status(self, doc, status):
        node = etree.SubElement(doc, 'state')
        node.set('state_id', self._status_id(status))
        node.set('title', status.title.decode('utf-8'))

        for transition in self.specification.transitions:
            assert transition.src_status is not None, \
                '%s has improperly defined src_status' % str(transition)
            if transition.src_status != status:
                continue

            exit_trans = etree.SubElement(node, 'exit-transition')
            exit_trans.set('transition_id', self._transition_id(transition))

        return node

    def _add_transition(self, doc, transition):
        node = etree.SubElement(doc, 'transition')

        node.set('new_state', self._status_id(transition.dest_status))
        node.set('title', transition.title.decode('utf-8'))
        node.set('transition_id', self._transition_id(transition))

        node.set('after_script', '')
        node.set('before_script', '')
        node.set('trigger', 'USER')

        action = etree.SubElement(node, 'action')
        action.set('category', 'workflow')
        action.set('icon', '')

        url_struct = self.specification.custom_transition_url or \
            '%%(content_url)s/content_status_modify' + \
            '?workflow_action=%(transition)s'

        action.set('url', url_struct % {
                'transition': self._transition_id(transition)})
        action.text = transition.title.decode('utf-8')

        return node

    def _apply_specification_statements(self, status_nodes,
                                        transition_nodes):
        transition_statements = dict([(status, set()) for status in
                                      status_nodes.keys()])

        per_status_role_inheritance = {}

        for status, snode in sorted(status_nodes.items(),
                                    key=lambda item: item[0].title):
            statements = set(status.statements) | set(
                self.specification.generals)

            role_inheritance = merge_role_inheritance(self.specification,
                                                      status)
            per_status_role_inheritance[status] = role_inheritance

            status_stmts, trans_stmts = self._distinguish_statements(
                statements)
            transition_statements[status].update(trans_stmts)

            self._apply_status_statements(snode, status_stmts,
                                          role_inheritance)

            self._add_worklist_when_necessary(status, role_inheritance)

        self._apply_transition_statements(transition_statements,
                                          transition_nodes,
                                          per_status_role_inheritance)

    def _apply_status_statements(self, snode, statements, role_inheritance):
        for permission in self.managed_permissions:
            pnode = etree.SubElement(snode, 'permission-map')
            pnode.set('name', permission)
            pnode.set('acquired', 'False')

            roles = self._get_roles_for_permission(permission, statements)
            roles = get_roles_inheriting_from(roles, role_inheritance)

            for role in roles:
                rolenode = etree.SubElement(pnode, 'permission-role')
                rolenode.text = role.decode('utf-8')

    def _apply_transition_statements(self, statements, nodes,
                                     per_status_role_inheritance):
        for transition, node in nodes.items():
            guards = etree.SubElement(node, 'guard')

            role_inheritance = per_status_role_inheritance.get(
                transition.src_status, [])

            roles = []
            for customer_role, action in statements[transition.src_status]:
                if action != transition.title:
                    continue

                role = self.specification.role_mapping[customer_role]
                roles.append(role)

            roles = get_roles_inheriting_from(roles, role_inheritance)

            for role in roles:
                rolenode = etree.SubElement(guards, 'guard-role')
                rolenode.text = role.decode('utf-8')

            if len(guards) == 0:
                # Disable the transition by a condition guard, because there
                # were no statements about who can do the transtion.
                xprnode = etree.SubElement(guards, 'guard-expression')
                xprnode.text = u'python: False'

    def _add_worklist_when_necessary(self, status, role_inheritance):
        if not status.worklist_viewers:
            return False

        worklist = etree.SubElement(self.document, 'worklist')
        worklist.set('title', '')
        worklist.set('worklist_id', self._worklist_id(status))

        action = etree.SubElement(worklist, 'action')
        action.set('category', 'global')
        action.set('icon', '')
        action.set('url', '%%(portal_url)s/search?review_state=%s' % (
                self._status_id(status)))
        action.text = '%s (%%(count)d)' % status.title.decode('utf-8')

        match = etree.SubElement(worklist, 'match')
        match.set('name', 'review_state')
        match.set('values', self._status_id(status))

        guards = etree.SubElement(worklist, 'guard')

        roles = [self.specification.role_mapping[crole]
                 for crole in status.worklist_viewers]
        roles = get_roles_inheriting_from(roles, role_inheritance)

        for role in sorted(roles):
            rolenode = etree.SubElement(guards, 'guard-role')
            rolenode.text = role.decode('utf-8')

    def _get_roles_for_permission(self, permission, statements):
        if permission in self.ignored_delegate_permissions:
            return []

        agregistry = getUtility(IActionGroupRegistry)
        action_groups = agregistry.get_action_groups_for_permission(
            permission, self.workflow_id)

        customer_roles = (role for (role, group) in statements
                          if group in action_groups)

        plone_roles = (self.specification.role_mapping[cr]
                       for cr in customer_roles)

        plone_roles = self._filter_delegate_roles_for_permissions(
            plone_roles, permission)
        return sorted(plone_roles)

    def _filter_delegate_roles_for_permissions(self, plone_roles, permission):
        return plone_roles

    def _distinguish_statements(self, statements):
        """Accepts a list of statements (tuples with customer role and action)
        and turns it into two lists, the first with action group statements,
        the second with transition statements.
        """

        action_group_statements = []
        transition_statements = []

        agregistry = getUtility(IActionGroupRegistry)
        action_groups = agregistry.get_action_groups_for_workflow(
            self.workflow_id)

        lang_code = self.specification.language.code
        translated_action_groups = dict(
            [(self._translate_action_group(name, lang_code), name)
             for name in action_groups])

        for customer_role, action in statements:
            if self._find_transition_by_title(action):
                transition_statements.append((customer_role, action))

            elif action in translated_action_groups:
                action_group_statements.append(
                    (customer_role, translated_action_groups[action]))

            else:
                raise Exception(
                    'Action "%s" is neither action group nor transition.' % (
                        action))

        return action_group_statements, transition_statements

    def _find_transition_by_title(self, title):
        for transition in self.specification.transitions:
            if transition.title == title:
                return transition
        return None

    def _add_variables(self, doc):
        # The variables are static - we use always the same.
        for node in html.fragments_fromstring(VARIABLES):
            node.tail = None
            doc.append(node)

    def _transition_id(self, transition):
        return '%s--TRANSITION--%s--%s_%s' % (
            self.workflow_id,
            self._normalize(transition.title),
            self._normalize(transition.src_status.title),
            self._normalize(transition.dest_status.title))

    def _status_id(self, status):
        return '%s--STATUS--%s' % (
            self.workflow_id, self._normalize(status.title))

    def _role_id(self, role):
        return generate_role_translation_id(self.workflow_id, role)

    def _role_description_id(self, role):
        return '%s--ROLE-DESCRIPTION--%s' % (
            self.workflow_id, getattr(role, 'original', role))

    def _worklist_id(self, status):
        return '%s--WORKLIST--%s' % (
            self.workflow_id, self._normalize(status.title))

    def _normalize(self, text):
        if isinstance(text, str):
            text = text.decode('utf-8')

        normalizer = getUtility(INormalizer)
        result = normalizer.normalize(text)
        return result.decode('utf-8')

    def _translate_action_group(self, action_group, language):
        zcml_domain = translate(action_group, target_language=language)
        if zcml_domain != action_group:
            return zcml_domain.encode('utf-8')
        else:
            return translate(unicode(action_group),
                             domain='ftw.lawgiver',
                             target_language=language).encode('utf-8')
