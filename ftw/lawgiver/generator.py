from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.variables import VARIABLES
from lxml import etree
from lxml import html
from plone.i18n.normalizer.interfaces import INormalizer
from zope.component import getUtility
from zope.interface import implements


class WorkflowGenerator(object):

    implements(IWorkflowGenerator)

    def __init__(self):
        self.workflow_id = None
        self.specification = None
        self.managed_permissions = None

    def __call__(self, workflow_id, specification, result_stream):
        self.workflow_id = workflow_id
        self.specification = specification
        self.managed_permissions = sorted(
            getUtility(IPermissionCollector).collect(workflow_id))

        doc = self._create_document()

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
        etree.ElementTree(doc).write(result_stream,
                                     pretty_print=True,
                                     xml_declaration=True,
                                     encoding='utf-8')

    def _create_document(self):
        root = etree.Element("dc-workflow")
        root.set('workflow_id', self.workflow_id)
        root.set('title', self.specification.title.decode('utf-8'))
        root.set('description', self.specification.description and
                 self.specification.description.decode('utf-8') or '')

        root.set('initial_state', self._status_id(
                self.specification.get_initial_status()))

        root.set('state_variable', 'review_state')
        root.set('manager_bypass', 'False')

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
        action.set('url', '%%(content_url)s/content_status_modify'
                   '?workflow_action=%s' % self._transition_id(transition))
        action.text = transition.title.decode('utf-8')

        return node

    def _apply_specification_statements(self, status_nodes, transition_nodes):
        transition_statements = dict([(status, set()) for status in
                                      status_nodes.keys()])

        for status, snode in status_nodes.items():
            statements = set(status.statements) | set(
                self.specification.generals)

            status_stmts, trans_stmts = self._distinguish_statements(
                statements)
            transition_statements[status].update(trans_stmts)
            self._apply_status_statements(snode, status_stmts)

        self._apply_transition_statements(transition_statements,
                                          transition_nodes)

    def _apply_status_statements(self, snode, statements):
        for permission in self.managed_permissions:
            pnode = etree.SubElement(snode, 'permission-map')
            pnode.set('name', permission)
            pnode.set('acquired', 'False')

            for role in self._get_roles_for_permission(permission,
                                                       statements):
                rolenode = etree.SubElement(pnode, 'permission-role')
                rolenode.text = role.decode('utf-8')

    def _apply_transition_statements(self, statements, nodes):
        for transition, node in nodes.items():
            guards = etree.SubElement(node, 'guard')

            for customer_role, action in statements[transition.src_status]:
                if action != transition.title:
                    continue

                role = self.specification.role_mapping[customer_role]
                rolenode = etree.SubElement(guards, 'guard-role')
                rolenode.text = role.decode('utf-8')

            if len(guards) == 0:
                # Disable the transition by a condition guard, because there
                # were no statements about who can do the transtion.
                xprnode = etree.SubElement(guards, 'guard-expression')
                xprnode.text = u'python: False'

    def _get_roles_for_permission(self, permission, statements):
        agregistry = getUtility(IActionGroupRegistry)
        action_group = agregistry.get_action_group_for_permission(permission)

        customer_roles = (role for (role, group) in statements
                          if group == action_group)

        plone_roles = (self.specification.role_mapping[cr]
                       for cr in customer_roles)
        return sorted(plone_roles)

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

        for customer_role, action in statements:
            if self._find_transition_by_title(action):
                transition_statements.append((customer_role, action))

            elif action in action_groups:
                action_group_statements.append((customer_role, action))

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

    def _normalize(self, text):
        if isinstance(text, str):
            text = text.decode('utf-8')

        normalizer = getUtility(INormalizer)
        result = normalizer.normalize(text)
        return result.decode('utf-8')
