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

        for status in sorted(specification.states.values(),
                             key=lambda status: status.title):
            self._add_status(doc, status)

        for transition in sorted(specification.transitions,
                                 key=lambda transition: transition.title):
            self._add_transition(doc, transition)

        self._add_variables(doc)
        etree.ElementTree(doc).write(result_stream,
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

        for permission in self.managed_permissions:
            self._add_status_permission(node, status, permission)

        return node

    def _add_status_permission(self, status_node, status, permission):
        node = etree.SubElement(status_node, 'permission-map')
        node.set('name', permission)
        node.set('acquired', 'False')

        agregistry = getUtility(IActionGroupRegistry)
        action_group = agregistry.get_action_group_for_permission(permission)
        roles = self.specification.get_roles_for_action_group_in_status(
            action_group, status)

        for role in roles:
            rolenode = etree.SubElement(node, 'permission-role')
            rolenode.text = role.decode('utf-8')

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

        roles = self.specification.get_roles_for_action_group_in_status(
            transition.title, transition.src_status)
        guards = etree.SubElement(node, 'guard')
        if roles:
            for role in roles:
                rolenode = etree.SubElement(guards, 'guard-role')
                rolenode.text = role.decode('utf-8')

        else:
            # Disable the transition by a condition guard, because there
            # were no statements about who can do the transtion.
            xprnode = etree.SubElement(guards, 'guard-expression')
            xprnode.text = u'python: False'

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
