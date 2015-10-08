from StringIO import StringIO
from ftw.lawgiver.collector import DefaultPermissionCollector
from ftw.lawgiver.generator import WorkflowGenerator
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.tests import workflowxml
from ftw.lawgiver.tests.base import BaseTest
from ftw.lawgiver.wdl.specification import Specification
from ftw.lawgiver.wdl.specification import Status
from ftw.lawgiver.wdl.specification import Transition
from ftw.testing import ComponentRegistryLayer
from zope.component import getGlobalSiteManager


class GeneratorLayer(ComponentRegistryLayer):

    def setUp(self):
        super(GeneratorLayer, self).setUp()

        import ftw.lawgiver.tests
        self.load_zcml_file('generator.zcml', ftw.lawgiver.tests)


GENERATOR_ZCML = GeneratorLayer()


class TestGenerator(BaseTest):

    layer = GENERATOR_ZCML

    def setUp(self):
        super(TestGenerator, self).setUp()
        getGlobalSiteManager().registerUtility(
            factory=DefaultPermissionCollector,
            provided=IPermissionCollector)

        # The IActionGroupRegistry utility registration is lazy.
        # Map a fake permission so that the utility is registered.
        self.map_permissions(['__fake_permission__'],
                             '__force_registry_registration__')

        import plone.i18n.normalizer
        self.layer.load_zcml_file('configure.zcml', plone.i18n.normalizer)

    def test_simple_workflow(self):
        spec = Specification(title='Example Workflow',
                             description='the Description',
                             initial_status_title='Foo')
        spec.states['Foo'] = Status('Foo', [])
        spec.validate()

        result = StringIO()
        WorkflowGenerator()('example-workflow', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'example-workflow',
            'title': 'Example Workflow',
            'description': 'the Description',
            'initial_status': 'example-workflow--STATUS--foo'} % (

            workflowxml.STATUS_STANDALONE % {
                'title': 'Foo',
                'id': 'example-workflow--STATUS--foo',
                })

        self.assert_xml(expected, result.getvalue())

    def test_multi_word_utf8_status_titles(self):
        status_title = 'Hello W\xc3\xb6rld'
        spec = Specification(title='W\xc3\xb6rkflow',
                             initial_status_title=status_title)
        spec.states[status_title] = Status(status_title, [])
        spec.validate()

        result = StringIO()
        WorkflowGenerator()('workflow', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'workflow',
            'title': 'W\xc3\xb6rkflow',
            'description': '',
            'initial_status': 'workflow--STATUS--hello-world'} % (

            workflowxml.STATUS_STANDALONE % {
                'title': status_title,
                'id': 'workflow--STATUS--hello-world',
                })

        self.assert_xml(expected, result.getvalue())

    def test_workflow_with_transitions(self):
        spec = Specification(title='WF',
                             initial_status_title='Foo')
        foo = spec.states['Foo'] = Status('Foo', [])
        bar = spec.states['Bar'] = Status('Bar', [])

        spec.transitions.append(Transition('b\xc3\xa4rize', foo, bar))
        spec.transitions.append(Transition('f\xc3\xbcize', bar, foo))
        spec.validate()

        result = StringIO()
        WorkflowGenerator()('workflow', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'workflow',
            'title': 'WF',
            'description': '',
            'initial_status': 'workflow--STATUS--foo'} % ''.join((

                workflowxml.STATUS % {
                    'title': 'Bar',
                    'id': 'workflow--STATUS--bar',
                    } % (workflowxml.EXIT_TRANSITION %
                         'workflow--TRANSITION--fuize--bar_foo'),

                workflowxml.STATUS % {
                    'title': 'Foo',
                    'id': 'workflow--STATUS--foo',
                    } % (workflowxml.EXIT_TRANSITION %
                         'workflow--TRANSITION--barize--foo_bar'),

                workflowxml.TRANSITION % {
                    'id': 'workflow--TRANSITION--barize--foo_bar',
                    'title': 'b\xc3\xa4rize',
                    'target_state': 'workflow--STATUS--bar',
                    'guards': workflowxml.GUARDS_DISABLED},

                workflowxml.TRANSITION % {
                    'id': 'workflow--TRANSITION--fuize--bar_foo',
                    'title': 'f\xc3\xbcize',
                    'target_state': 'workflow--STATUS--foo',
                    'guards': workflowxml.GUARDS_DISABLED},

                ))

        self.assert_xml(expected, result.getvalue())

    def test_workflow_with_custom_transition_url(self):
        spec = Specification(
            title='WF',
            initial_status_title='Foo',
            custom_transition_url='%%(content_url)s/custom_wf_action'
            '?workflow_action=%(transition)s')
        foo = spec.states['Foo'] = Status('Foo', [])
        bar = spec.states['Bar'] = Status('Bar', [])

        spec.transitions.append(Transition('b\xc3\xa4rize', foo, bar))
        spec.transitions.append(Transition('f\xc3\xbcize', bar, foo))
        spec.validate()

        result = StringIO()
        WorkflowGenerator()('workflow', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'workflow',
            'title': 'WF',
            'description': '',
            'initial_status': 'workflow--STATUS--foo'} % ''.join((

                workflowxml.STATUS % {
                    'title': 'Bar',
                    'id': 'workflow--STATUS--bar',
                    } % (workflowxml.EXIT_TRANSITION %
                         'workflow--TRANSITION--fuize--bar_foo'),

                workflowxml.STATUS % {
                    'title': 'Foo',
                    'id': 'workflow--STATUS--foo',
                    } % (workflowxml.EXIT_TRANSITION %
                         'workflow--TRANSITION--barize--foo_bar'),

                workflowxml.TRANSITION_WITH_CUSTOM_URL % {
                    'id': 'workflow--TRANSITION--barize--foo_bar',
                    'title': 'b\xc3\xa4rize',
                    'target_state': 'workflow--STATUS--bar',
                    'guards': workflowxml.GUARDS_DISABLED,
                    'url_viewname': 'custom_wf_action'},

                workflowxml.TRANSITION_WITH_CUSTOM_URL % {
                    'id': 'workflow--TRANSITION--fuize--bar_foo',
                    'title': 'f\xc3\xbcize',
                    'target_state': 'workflow--STATUS--foo',
                    'guards': workflowxml.GUARDS_DISABLED,
                    'url_viewname': 'custom_wf_action'},

                ))

        self.assert_xml(expected, result.getvalue())

    def test_workflow_with_managed_permissions(self):
        self.register_permissions(**{
                'cmf.ModifyPortalContent': 'Modify portal content',
                'zope2.View': 'View',
                'zope2.AccessContentsInformation': \
                    'Access contents information',
                'cmf.ManagePortal': 'Manage portal'})

        self.map_permissions(['View', 'Access contents information'], 'view')
        self.map_permissions(['Modify portal content'], 'edit')
        self.map_permissions(['Manage portal'], 'manage')

        spec = Specification(title='Workflow',
                             initial_status_title='Foo')
        spec.role_mapping['writer'] = 'Editor'
        spec.role_mapping['admin'] = 'Administrator'

        spec.states['Foo'] = Status('Foo', [
                ('writer', 'view'),
                ('writer', 'edit'),
                ('admin', 'view'),
                ('admin', 'manage')])
        spec.validate()

        result = StringIO()
        WorkflowGenerator()('example-workflow', spec).write(result)


        xml_permissions_declaration = ''.join((
                workflowxml.PERMISSION % 'Access contents information',
                workflowxml.PERMISSION % 'Manage portal',
                workflowxml.PERMISSION % 'Modify portal content',
                workflowxml.PERMISSION % 'View',
                ))

        xml_status_defininition = workflowxml.STATUS % {
            'title': 'Foo',
            'id': 'example-workflow--STATUS--foo',
            } % ''.join((

                (workflowxml.PERMISSION_MAP %
                 'Access contents information') % ''.join((
                        workflowxml.PERMISSION_ROLE % 'Administrator',
                        workflowxml.PERMISSION_ROLE % 'Editor')),

                (workflowxml.PERMISSION_MAP % 'Manage portal') % (
                    workflowxml.PERMISSION_ROLE % 'Administrator'),

                (workflowxml.PERMISSION_MAP % 'Modify portal content') % (
                    workflowxml.PERMISSION_ROLE % 'Editor'),

                (workflowxml.PERMISSION_MAP % 'View') % ''.join((
                        workflowxml.PERMISSION_ROLE % 'Administrator',
                        workflowxml.PERMISSION_ROLE % 'Editor')),
                ))

        expected = workflowxml.WORKFLOW % {
            'id': 'example-workflow',
            'title': 'Workflow',
            'description': '',
            'initial_status': 'example-workflow--STATUS--foo'} % ''.join((
                xml_permissions_declaration,
                xml_status_defininition))

        self.assert_xml(expected, result.getvalue())

    def test_workflow_guarded_transitions(self):
        spec = Specification(title='Workflow',
                             initial_status_title='Private')
        spec.role_mapping['employee'] = 'Editor'
        spec.role_mapping['boss'] = 'Reviewer'

        private = spec.states['Private'] = Status('Private', [
                ('employee', 'publish'),
                ('boss', 'publish')])

        published = spec.states['Published'] = Status('Published', [
                ('boss', 'retract')])

        spec.transitions.append(Transition('publish', private, published))
        spec.transitions.append(Transition('retract', published, private))

        spec.validate()

        result = StringIO()
        WorkflowGenerator()('wf', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'wf',
            'title': 'Workflow',
            'description': '',
            'initial_status': 'wf--STATUS--private'} % ''.join((

                workflowxml.STATUS % {
                    'title': 'Private',
                    'id': 'wf--STATUS--private',
                    } % workflowxml.EXIT_TRANSITION % (
                    'wf--TRANSITION--publish--private_published'),

                workflowxml.STATUS % {
                    'title': 'Published',
                    'id': 'wf--STATUS--published',
                    } % workflowxml.EXIT_TRANSITION % (
                    'wf--TRANSITION--retract--published_private'),

                workflowxml.TRANSITION % {
                    'id': 'wf--TRANSITION--publish--private_published',
                    'title': 'publish',
                    'target_state': 'wf--STATUS--published',
                    'guards': workflowxml.GUARDS % ''.join((
                            workflowxml.GUARD_ROLE % 'Editor',
                            workflowxml.GUARD_ROLE % 'Reviewer',
                            ))},

                workflowxml.TRANSITION % {
                    'id': 'wf--TRANSITION--retract--published_private',
                    'title': 'retract',
                    'target_state': 'wf--STATUS--private',
                    'guards': workflowxml.GUARDS % (
                        workflowxml.GUARD_ROLE % 'Reviewer',
                        )},

                ))

        self.assert_definition_xmls(expected, result.getvalue())

    def test_workflow_with_unkown_action_raises(self):
        self.register_permissions(**{
                'cmf.ModifyPortalContent': 'Modify portal content',
                'zope2.View': 'View',
                'zope2.AccessContentsInformation': \
                    'Access contents information'})

        self.map_permissions(['View', 'Access contents information'], 'view')
        self.map_permissions(['Modify portal content'], 'edit')

        spec = Specification(title='Workflow',
                             initial_status_title='Foo')
        spec.role_mapping['writer'] = 'Editor'
        spec.role_mapping['admin'] = 'Administrator'

        foo = spec.states['Foo'] = Status('Foo', [
                ('writer', 'view'),
                ('writer', 'edit'),
                ('writer', 'publish'),
                ('admin', 'view'),
                ('admin', 'publish'),
                ('admin', 'bar')])

        spec.transitions.append(Transition('publish', foo, foo))
        spec.validate()

        generator = WorkflowGenerator()

        with self.assertRaises(Exception) as cm:
            generator('example-workflow', spec)

        self.assertEquals('Action "bar" is neither action group nor transition.',
                          str(cm.exception))


    def test_get_translations(self):
        spec = Specification(title='Workflow',
                             initial_status_title='Private')
        spec.role_mapping['employee'] = 'Editor'
        spec.role_mapping['boss'] = 'Reviewer'

        spec.role_descriptions['employee'] = 'A regular company employee.'

        private = spec.states['Private'] = Status('Private', [
                ('employee', 'publish'),
                ('boss', 'publish')])

        published = spec.states['Published'] = Status('Published', [
                ('boss', 'retract')])

        spec.transitions.append(Transition('publish', private, published))
        spec.transitions.append(Transition('retract', published, private))

        spec.validate()

        result = WorkflowGenerator().get_translations('wf', spec)

        self.maxDiff = None
        self.assertEquals(
            {'Private': 'Private',
             'Published': 'Published',
             'publish': 'publish',
             'retract': 'retract',
             'wf--ROLE--Editor': 'employee',
             'wf--ROLE--Reviewer': 'boss',
             'wf--ROLE-DESCRIPTION--Editor': 'A regular company employee.',
             },

            result,
            'Translations are wrong')

    def test_get_states(self):
        spec = Specification(title='Workflow',
                             initial_status_title='Private')

        spec.states['Private'] = Status('Private', [])
        spec.states['Published'] = Status('Published', [])
        result = WorkflowGenerator().get_states('wf', spec)

        self.assertEquals(
            ['wf--STATUS--private',
             'wf--STATUS--published'],

            result,
            'Wrong state IDs in generator.get_states()')

    def test_inherited_roles(self):
        self.register_permissions(**{
                'cmf.ModifyPortalContent': 'Modify portal content',
                'zope2.View': 'View',
                'zope2.AccessContentsInformation': \
                    'Access contents information',
                'cmf.ManagePortal': 'Manage portal'})

        self.map_permissions(['View', 'Access contents information'], 'view')
        self.map_permissions(['Modify portal content'], 'edit')

        spec = Specification(
            title='Workflow',
            initial_status_title='Foo',
            # general inheritance
            role_inheritance=[('chief', 'admin')])

        spec.role_mapping['writer'] = 'Editor'
        spec.role_mapping['admin'] = 'Administrator'
        spec.role_mapping['chief'] = 'Manager'
        spec.role_mapping['reader'] = 'Reader'

        spec.states['Foo'] = foo = Status(
            'Foo',
            [('writer', 'view'),
             ('writer', 'edit'),
             ('writer', 'publish')],

            # inheritance in status
            role_inheritance=[('admin', 'writer'),
                              ('reader', 'chief')])

        spec.states['Bar'] = bar = Status(
            'Bar',
            [('admin', 'retract')])

        spec.transitions.append(Transition('publish', foo, bar))
        spec.transitions.append(Transition('retract', bar, foo))

        spec.validate()

        result = StringIO()
        WorkflowGenerator()('example-workflow', spec).write(result)

        xml_permissions_declaration = ''.join((
                workflowxml.PERMISSION % 'Access contents information',
                workflowxml.PERMISSION % 'Modify portal content',
                workflowxml.PERMISSION % 'View',
                ))

        xml_foo_defininition = workflowxml.STATUS % {
            'title': 'Foo',
            'id': 'example-workflow--STATUS--foo',
            } % ''.join((

                workflowxml.EXIT_TRANSITION % (
                    'example-workflow--TRANSITION--publish--foo_bar'),

                (workflowxml.PERMISSION_MAP %
                 'Access contents information') % ''.join((
                        workflowxml.PERMISSION_ROLE % 'Administrator',
                        workflowxml.PERMISSION_ROLE % 'Editor',
                        workflowxml.PERMISSION_ROLE % 'Manager',
                        workflowxml.PERMISSION_ROLE % 'Reader')),

                (workflowxml.PERMISSION_MAP %
                 'Modify portal content') % ''.join((
                        workflowxml.PERMISSION_ROLE % 'Administrator',
                        workflowxml.PERMISSION_ROLE % 'Editor',
                        workflowxml.PERMISSION_ROLE % 'Manager',
                        workflowxml.PERMISSION_ROLE % 'Reader')),

                (workflowxml.PERMISSION_MAP % 'View') % ''.join((
                        workflowxml.PERMISSION_ROLE % 'Administrator',
                        workflowxml.PERMISSION_ROLE % 'Editor',
                        workflowxml.PERMISSION_ROLE % 'Manager',
                        workflowxml.PERMISSION_ROLE % 'Reader')),
                ))

        xml_bar_defininition = workflowxml.STATUS % {
            'title': 'Bar',
            'id': 'example-workflow--STATUS--bar',
            } % ''.join((

                workflowxml.EXIT_TRANSITION % (
                    'example-workflow--TRANSITION--retract--bar_foo'),

                workflowxml.EMPTY_PERMISSION_MAP % (
                    'Access contents information'),
                workflowxml.EMPTY_PERMISSION_MAP % 'Modify portal content',
                workflowxml.EMPTY_PERMISSION_MAP % 'View',
                ))

        xml_publish_transition = workflowxml.TRANSITION % {
            'id': 'example-workflow--TRANSITION--publish--foo_bar',
            'title': 'publish',
            'target_state': 'example-workflow--STATUS--bar',
            'guards': workflowxml.GUARDS % ''.join((
                    workflowxml.GUARD_ROLE % 'Administrator',
                    workflowxml.GUARD_ROLE % 'Editor',
                    workflowxml.GUARD_ROLE % 'Manager',
                    workflowxml.GUARD_ROLE % 'Reader',
                    ))}

        xml_retract_transition = workflowxml.TRANSITION % {
            'id': 'example-workflow--TRANSITION--retract--bar_foo',
            'title': 'retract',
            'target_state': 'example-workflow--STATUS--foo',
            'guards': workflowxml.GUARDS % ''.join((
                    workflowxml.GUARD_ROLE % 'Administrator',
                    workflowxml.GUARD_ROLE % 'Manager',
                    ))}

        expected = workflowxml.WORKFLOW % {
            'id': 'example-workflow',
            'title': 'Workflow',
            'description': '',
            'initial_status': 'example-workflow--STATUS--foo'} % ''.join((
                xml_permissions_declaration,
                xml_bar_defininition,
                xml_foo_defininition,
                xml_publish_transition,
                xml_retract_transition))

        self.assert_xml(expected, result.getvalue())

    def test_worklists(self):
        spec = Specification(title='Workflow',
                             initial_status_title='Pending')
        spec.role_mapping['employee'] = 'Editor'
        spec.role_mapping['boss'] = 'Reviewer'

        spec.states['Pending'] = Status(
            'Pending', [],
            worklist_viewers=['employee', 'boss'])

        spec.validate()

        result = StringIO()
        WorkflowGenerator()('wf', spec).write(result)

        expected = workflowxml.WORKFLOW % {
            'id': 'wf',
            'title': 'Workflow',
            'description': '',
            'initial_status': 'wf--STATUS--pending'} % ''.join((

                workflowxml.STATUS_STANDALONE % {
                    'title': 'Pending',
                    'id': 'wf--STATUS--pending',
                    },

                workflowxml.WORKLIST % {
                    'id': 'wf--WORKLIST--pending',
                    'status_id': 'wf--STATUS--pending',
                    'status_title': 'Pending',
                    'guards': workflowxml.GUARDS % ''.join((
                            workflowxml.GUARD_ROLE % 'Editor',
                            workflowxml.GUARD_ROLE % 'Reviewer',
                            ))
                    },

                ))

        self.assert_definition_xmls(expected, result.getvalue())
