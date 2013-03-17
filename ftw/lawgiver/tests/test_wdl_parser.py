from StringIO import StringIO
from ftw.lawgiver.exceptions import ParsingError
from ftw.lawgiver.testing import WDL_ZCML
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.lawgiver.wdl.parser import convert_statement
from unittest2 import TestCase
from zope.component import getUtility
from zope.component import queryUtility
from zope.interface.verify import verifyObject


class TestParser(TestCase):

    layer = WDL_ZCML

    def parse_lines(self, *lines):
        parser = getUtility(IWorkflowSpecificationParser)
        stream = StringIO('\n'.join(lines))
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

    def test_only_one_section_allowd(self):
        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(
                '[foo]',
                '',
                '[bar]')

        self.assertEquals('Exactly one ini-style section is required, '
                          'containing the workflow title.',
                          str(cm.exception))

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
        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(
            '[Foo]',
            '',
            'Transitions:',
            '  this is invalid')

        self.assertEquals(
            'Transition line has an invalid format: "this is invalid"',
            str(cm.exception))

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
        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(
                '[Foo]',
                'Role Mapping:',
                '  this is wrong')

        self.assertEquals(
            'Invalid format in role mapping: "this is wrong"',
            str(cm.exception))

    def test_general_statements(self):
        spec = self.parse_lines(
            '[Foo]',
            '',
            'General:',
            '  An administrator can always view this content')

        self.assertEquals([('administrator', 'view')],
                          spec.generals)

    def test_fails_when_no_consumer_for_option(self):
        with self.assertRaises(ParsingError) as cm:
            self.parse_lines(
                '[Foo]',
                'bar = baz')

        self.assertEquals('The option "bar" is not valid.',
                          str(cm.exception))


class TestConvertStatement(TestCase):

    def assert_statement(self, expected_result, text):
        result = convert_statement(text)
        self.assertEquals(
            expected_result, result,
            'Wrong result when converting statement:' +
            ' expected "%s", got "%s"' % (expected_result, result) +
            '\nStatement: "%s"' % text)

    def test_simple_context_specific_statements(self):
        self.assert_statement(('editor', 'view'),
                              'An editor can view this content.')

        self.assert_statement(('supervisor', 'edit'),
                              'A supervisor can edit this content')

    def test_anyone_statements(self):
        self.assert_statement(('anyone', 'view'),
                              'Anyone can view this content.')

    def test_context_less_statements(self):
        self.assert_statement(('editor', 'publish'),
                              'An editor can publish.')

    def test_multi_word_statements(self):
        self.assert_statement(
            ('editor in chief', 'manage portlets'),
            'A editor in chief can manage portlets on this context.')

    def test_always_statements(self):
        self.assert_statement(
            ('administrator', 'view'),
            'An administrator can always view this content.')

    def test_add_new_content_statements(self):
        self.assert_statement(
            ('editor', 'add'),
            'An editor can add new content.')

        self.assert_statement(
            ('editor', 'add'),
            'An editor can add content.')

    def test_bad_statement(self):
        with self.assertRaises(ParsingError) as cm:
            convert_statement('This is not a statement.')

        self.assertEquals(
            'Unkown statement format: "This is not a statement."',
            str(cm.exception))
