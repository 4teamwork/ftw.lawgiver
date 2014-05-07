from StringIO import StringIO
from ftw.lawgiver.exceptions import ParsingError
from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.lawgiver.wdl.languages import LANGUAGES
from ftw.lawgiver.wdl.parser import PERMISSION_STATEMENT
from ftw.lawgiver.wdl.parser import WORKLIST_STATEMENT
from ftw.lawgiver.wdl.parser import convert_statement
from ftw.testing import MockTestCase
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface.verify import verifyObject


class TestParser(MockTestCase):

    layer = ZCML_FIXTURE

    def parse_lines(self, *lines, **kwargs):
        parser = getUtility(IWorkflowSpecificationParser)
        stream = StringIO('\n'.join(lines))
        if kwargs.get('silent'):
            return parser(stream, silent=True)
        else:
            return parser(stream)

    def test_component_registered(self):
        self.assertTrue(
            queryUtility(IWorkflowSpecificationParser),
            'IWorkflowSpecificationParser utility not registered')

    def test_implements_interface(self):
        parser = getUtility(IWorkflowSpecificationParser)
        self.assertTrue(IWorkflowSpecificationParser.providedBy(parser))
        verifyObject(IWorkflowSpecificationParser, parser)

    def test_parser_returns_specification_object(self):
        result = self.parse_lines(
            '[a Workflow]')

        self.assertTrue(ISpecification.providedBy(result),
                        'parser result is not an ISpecification')

        self.assertEquals(result.title, 'a Workflow')

    def test_only_one_section_allowed(self):
        lines = (
            '[foo]',
            '',
            '[bar]')

        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(*lines)

        self.assertEquals('Exactly one ini-style section is required, '
                          'containing the workflow title.',
                          str(cm.exception))

        self.assertEquals(
            None, self.parse_lines(*lines, silent=True),
            'Parser should not raise an exception when silent=True')

    def test_description(self):
        spec = self.parse_lines(
            '[foo]',
            'Description: The Description')

        self.assertEquals(spec.description, 'The Description')

    def test_description_lowercase(self):
        spec = self.parse_lines(
            '[foo]',
            'description: The Description')

        self.assertEquals(spec.description, 'The Description')

    def test_transition_url(self):
        spec = self.parse_lines('[foo]')
        self.assertEquals(spec.custom_transition_url, None)

        spec = self.parse_lines(
            '[foo]',
            'Transition-URL = foo?id=%(transition)s')

        self.assertEquals(spec.custom_transition_url, 'foo?id=%(transition)s')

        spec = self.parse_lines(
            '[foo]',
            'transition-url = foo?id=%(transition)s')

        self.assertEquals(spec.custom_transition_url, 'foo?id=%(transition)s')

    def test_states(self):
        spec = self.parse_lines(
            '[Foo]',
            'Initial status: Private'
            '',
            'Status Private:',
            '  An editor can view this content.',
            '',
            'Status Public:',
            '  An editor can view this content.')

        self.assertEquals(
            {'Private': u'<Status "Private">',
             'Public': u'<Status "Public">'},

            dict(map(lambda item: (item[0], unicode(item[1])),
                     spec.states.items())))

    def test_empty_status(self):
        # Let's support iteration based workflow development: I might
        # not define the details of the states from the beginning..

        spec = self.parse_lines(
            '[Foo]',
            'Initial status: Private',
            '',
            'Status Private:',
            '',
            'Status Pending:',
            ''
            'Status Published:')

        self.assertEquals(
            {'Private': u'<Status "Private">',
             'Pending': u'<Status "Pending">',
             'Published': u'<Status "Published">'},

            dict(map(lambda item: (item[0], unicode(item[1])),
                     spec.states.items())))

    def test_simple_context_specific_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            'Status Private:',
            '  An editor can view this content.',
            '  A supervisor can edit this content')

        self.assertEquals([('editor', 'view'),
                           ('supervisor', 'edit')],
                          spec.states['Private'].statements)

    def test_anyone_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            'Status Private:',
            '  Anyone can view this content.')

        # anyone should be lowercased when matching.
        self.assertEquals([('anyone', 'view')],
                          spec.states['Private'].statements)

    def test_context_less_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            'Status Private:',
            '  A editor can publish.')

        self.assertEquals([('editor', 'publish')],
                          spec.states['Private'].statements)

    def test_multi_word_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            'Status Private:',
            '  A editor in chief can manage portlets on this context.')

        self.assertEquals([('editor in chief', 'manage portlets')],
                          spec.states['Private'].statements)

    def test_transitions(self):
        spec = self.parse_lines(
            '[Foo]',
            ''
            'Status Private:',
            '  An editor can view this content.',
            '',
            'Status Published:',
            '  An editor can view this content.',
            '',
            'Transitions:',
            '  publish (Private => Published)',
            '  retract (Published => Private)')

        self.assertEquals(
            set(['<Transition "publish" ["Private" => "Published"]>',
                 '<Transition "retract" ["Published" => "Private"]>']),
            set(map(unicode, spec.transitions)))

    def test_invalid_transition_line(self):
        lines = (
            '[Foo]',
            '',
            'Transitions:',
            '  this is invalid')

        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(*lines)

        self.assertEquals(
            'Transition line has an invalid format: "this is invalid"',
            str(cm.exception))

        self.assertEquals(
            None, self.parse_lines(*lines, silent=True),
            'Parser should not raise an exception when silent=True')

    def test_role_mapping(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'Role mapping:',
            '  editor in-chief => Reviewer',
            '  admin => Site Administrator')

        self.assertEquals({'editor in-chief': 'Reviewer',
                           'admin': 'Site Administrator'},
                          spec.role_mapping)

    def test_invalid_role_mapping_line(self):
        lines = (
            '[Foo]',
            'Role Mapping:',
            '  this is wrong')

        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(*lines)

        self.assertEquals(
            'Invalid format in role mapping: "this is wrong"',
            str(cm.exception))

        self.assertEquals(
            None, self.parse_lines(*lines, silent=True),
            'Parser should not raise an exception when silent=True')

    def test_visible_roles(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'Role mapping:',
            '  editor => Editor',
            '  editor in-chief => Reviewer'
            '',
            'Visible roles:',
            '  editor',
            '  editor in-chief')

        self.assertEquals(['editor', 'editor in-chief'],
                          spec.visible_roles)

    def test_role_descriptions(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'Role mapping:',
            '  editor => Editor',
            '  editor in-chief => Reviewer'
            '',
            'Visible roles:',
            '  editor',
            '  editor in-chief',
            '',
            'editor role description:',
            '  The editor writes text.',
            'editor in-chief role description:'
            '  The editor in chief',
            '  reviews text.')

        self.assertEquals(
            {'editor': 'The editor writes text.',
             'editor in-chief': 'The editor in chief reviews text.'},
            spec.role_descriptions)

    def test_general_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'General:',
            '  An administrator can always view this content')

        self.assertEquals([('administrator', 'view')],
                          spec.generals)

    def test_fails_when_no_consumer_for_option(self):
        lines = (
            '[Foo]',
            'bar = baz')

        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(*lines)

        self.assertEquals('The option "bar" is not valid.',
                          str(cm.exception))

        self.assertEquals(
            None, self.parse_lines(*lines, silent=True),
            'Parser should not raise an exception when silent=True')

    def test_general_role_inheritance(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'General:',
            '  An administrator can always perform the same actions '
            'as an editor.')

        self.assertEquals([('administrator', 'editor')],
                          spec.role_inheritance)

    def test_status_role_inheritance(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'Status Foo:',
            '  An administrator can always perform the same as a editor.')

        self.assertEquals([],
                          spec.role_inheritance)

        self.assertEquals([('administrator', 'editor')],
                          spec.states.values()[0].role_inheritance)

    def test_worklist_viewers(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'Status Foo:',
            '  An Editor-In-Chief can access the worklist.',
            '  A reviewer can access the worklist.')

        self.assertEquals(
            ['editor-in-chief',
             'reviewer'],
            spec.states.values()[0].worklist_viewers)

    def test_general_worklists_not_possible(self):
        # Worklist statements in the "General:" section are not allowed
        # because it is too implicit: we cannot tell which states are
        # "review" states and should have worklists.

        # It would result in a worklist for each status, which would
        # always display all contents of the site in the worklist..

        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(
                '[Foo]',
                '',
                'General:',
                '  A reviewer can access the worklist.')

        self.assertEquals(
            str(cm.exception),
            'Worklist statements are not allowed in the "General" section.')


class TestConvertStatement(MockTestCase):

    def assert_statement(self, expected_result, text):
        result = convert_statement(LANGUAGES['en'], text)
        self.assertEquals(
            expected_result, result,
            'Wrong result when converting statement:' +
            ' expected "%s", got "%s"' % (expected_result, result) +
            '\nStatement: "%s"' % text)

    def test_simple_context_specific_statements(self):
        self.assert_statement((PERMISSION_STATEMENT, ('editor', 'view')),
                              'An editor can view this content.')

        self.assert_statement((PERMISSION_STATEMENT, ('supervisor', 'edit')),
                              'A supervisor can edit this content')

    def test_anyone_statements(self):
        self.assert_statement((PERMISSION_STATEMENT, ('anyone', 'view')),
                              'Anyone can view this content.')

    def test_context_less_statements(self):
        self.assert_statement((PERMISSION_STATEMENT, ('editor', 'publish')),
                              'An editor can publish.')

    def test_multi_word_statements(self):
        self.assert_statement(
            (PERMISSION_STATEMENT, ('editor in chief', 'manage portlets')),
            'A editor in chief can manage portlets on this context.')

    def test_always_statements(self):
        self.assert_statement(
            (PERMISSION_STATEMENT, ('administrator', 'view')),
            'An administrator can always view this content.')

    def test_any_statements(self):
        self.assert_statement(
            (PERMISSION_STATEMENT, ('administrator', 'delete')),
            'An administrator can delete any content.')

    def test_add_new_content_statements(self):
        self.assert_statement(
            (PERMISSION_STATEMENT, ('editor', 'add')),
            'An editor can add new content.')

        self.assert_statement(
            (PERMISSION_STATEMENT, ('editor', 'add')),
            'An editor can add content.')

    def test_bad_statement(self):
        with self.assertRaises(ParsingError) as cm:
            convert_statement(LANGUAGES['en'], 'This is not a statement.')

        self.assertEquals(
            'Unkown statement format: "This is not a statement."',
            str(cm.exception))

    def test_worklist_statement(self):
        self.assert_statement(
            (WORKLIST_STATEMENT, 'administrator'),
            'An Administrator can access the worklist.')

        self.assert_statement(
            (WORKLIST_STATEMENT, 'editor in chief'),
            'An Editor in chief can access the worklist.')
