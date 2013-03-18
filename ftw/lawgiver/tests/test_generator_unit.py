from StringIO import StringIO
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.tests import workflowxml
from ftw.lawgiver.tests.base import BaseTest
from ftw.lawgiver.wdl.specification import Specification
from ftw.lawgiver.wdl.specification import Status
from ftw.lawgiver.wdl.specification import Transition
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface.verify import verifyObject


class TestGenerator(BaseTest):

    layer = ZCML_FIXTURE

    def setUp(self):
        super(TestGenerator, self).setUp()
        import zope.security
        self.layer.load_zcml_file('meta.zcml', zope.security)

    def test_component_registered(self):
        self.assertTrue(queryUtility(IWorkflowGenerator),
                        'The IWorkflowGenerator utility is not registerd.')

    def test_component_implements_interface(self):
        component = getUtility(IWorkflowGenerator)
        self.assertTrue(IWorkflowGenerator.providedBy(component))

        verifyObject(IWorkflowGenerator, component)

    def test_simple_workflow(self):
        spec = Specification(title='Example Workflow',
                             description='the Description',
                             initial_status_title='Foo')
        spec.states['Foo'] = Status('Foo', [])
        spec.validate()

        result = StringIO()
        getUtility(IWorkflowGenerator)('example-workflow', spec, result)

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
        getUtility(IWorkflowGenerator)('workflow', spec, result)

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
        getUtility(IWorkflowGenerator)('workflow', spec, result)

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
                    'guards': ''},

                workflowxml.TRANSITION % {
                    'id': 'workflow--TRANSITION--fuize--bar_foo',
                    'title': 'f\xc3\xbcize',
                    'target_state': 'workflow--STATUS--foo',
                    'guards': ''},

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
        getUtility(IWorkflowGenerator)('example-workflow', spec, result)

        expected = workflowxml.WORKFLOW % {
            'id': 'example-workflow',
            'title': 'Workflow',
            'description': '',
            'initial_status': 'example-workflow--STATUS--foo'} % (

            workflowxml.STATUS % {
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
                    )))

        self.assert_xml(expected, result.getvalue())
