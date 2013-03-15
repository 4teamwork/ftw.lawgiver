from StringIO import StringIO
from ftw.lawgiver.testing import WDL_ZCML
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from unittest2 import TestCase
from zope.component import getUtility
from zope.schema.interfaces import ConstraintNotSatisfied
import os


class TestWDLIntegration(TestCase):

    layer = WDL_ZCML

    def parse(self, spec):
        parser = getUtility(IWorkflowSpecificationParser)
        return parser.parse(spec)

    def parse_lines(self, *lines):
        return self.parse(StringIO('\n'.join(lines)))

    def test_title_only_specification(self):
        ast = self.parse_lines(
            'Title: A fancy workflow',
            '')

        self.assertTrue(ISpecification.providedBy(ast))
        self.assertEquals('A fancy workflow', ast.title)

    def test_title_description_spec(self):
        ast = self.parse_lines(
            'Title: A fancy w\xc3\xb6rkflow',
            'Description: a rather fancy workflow, with many features.',
            '',
            )

        self.assertEquals(u'A fancy w\xf6rkflow', ast.title)
        self.assertEquals('a rather fancy workflow, with many features.',
                          ast.description)

    def test_spec_with_states(self):
        ast = self.parse_lines(
            'Title: A workflow',
            '',
            'States:',
            '- * Foo',
            '- Bar')

        self.assertEquals(len(ast.states), 2)
        foo, bar = ast.states

        self.assertEquals(foo.title, 'Foo')
        self.assertEquals(foo.init_status, True)

        self.assertEquals(bar.title, 'Bar')
        self.assertEquals(bar.init_status, False)

    def test_spec_with_transitions(self):
        ast = self.parse_lines(
            'Title: workflow',
            '',
            'States:',
            '- * Foo',
            '- Bar',
            '',
            'Transitions:',
            '- forward (Foo => Bar)',
            '- backward (Bar => Foo)')

        self.assertEquals(len(ast.transitions), 2)
        forward, backward = ast.transitions

        self.assertEquals(forward.title, 'forward')
        self.assertEquals(forward.get_from_status().title, 'Foo')
        self.assertEquals(forward.get_to_status().title, 'Bar')

        self.assertEquals(backward.title, 'backward')
        self.assertEquals(backward.get_from_status().title, 'Bar')
        self.assertEquals(backward.get_to_status().title, 'Foo')

    def test_spec_with_invalid_status_names_in_transitions(self):
        with self.assertRaises(ConstraintNotSatisfied) as cm:
            self.parse_lines(
                'Title: workflow',
                '',
                'States:',
                '- * Foo',
                '',
                'Transitions:',
                '- baz (Foo => Bar)')

        self.assertEquals('There is no status with title "Bar". (Line 7)',
                          str(cm.exception))

        with self.assertRaises(ConstraintNotSatisfied) as cm:
            self.parse_lines(
                'Title: workflow',
                '',
                'States:',
                '- * Bar',
                '',
                'Transitions:',
                '- baz (Foo => Bar)')

        self.assertEquals('There is no status with title "Foo". (Line 7)',
                          str(cm.exception))

    def test_spec_with_role_mapping(self):
        ast = self.parse_lines(
            'Title: another workflow',
            '',
            'Role mapping:',
            '- editor => Editor',
            '- admin => Site Administrator')

        self.assertEquals(len(ast.role_mappings), 2)
        editor, admin = ast.role_mappings

        self.assertEquals(editor.customer_role, 'editor')
        self.assertEquals(editor.plone_role, 'Editor')

        self.assertEquals(admin.customer_role, 'admin')
        self.assertEquals(admin.plone_role, 'Site Administrator')

    def test_spec_needs_an_initial_status(self):
        # REMARK: the validator fails only when at least one status is
        # defined but there is no initial state.
        # For the sake of simpleness it does not fail when no states
        # are defined at all (its easier to test and it allows to write
        # workflows incrementally).

        with self.assertRaises(ConstraintNotSatisfied) as cm:
            self.parse_lines(
                'Title: A workflow',
                '',
                'States:',
                '- Bar')

        self.assertEquals(
            'No initial status defined.'
            ' Add an asterisk (*) in front of the initial status.',
            str(cm.exception))

    def test_spec_allows_max_one_initial_status(self):
        # REMARK: the validator fails only when at least one status is
        # defined but there is no initial state.
        # For the sake of simpleness it does not fail when no states
        # are defined at all (its easier to test and it allows to write
        # workflows incrementally).

        with self.assertRaises(ConstraintNotSatisfied) as cm:
            self.parse_lines(
                'Title: A workflow',
                '',
                'States:',
                '- * Foo',
                '- Bar',
                '- * Baz')

        self.assertEquals(
            'You have defined multiple initial states, but there should'
            ' be exactly one (Lines 4, 6).',
            str(cm.exception))

    def test_example_specification(self):
        with open(os.path.join(
                os.path.dirname(__file__),
                'assets', 'example.specification.txt')) as file_:
            spec = self.parse(file_)

        # Properties
        self.assertEquals('My Custom Workflow', spec.title)
        self.assertEquals('A three state publication workflow',
                          spec.description)

        # States
        self.assertEquals(
            ['<Status "Private" [init]>',
             '<Status "Pending">',
             '<Status "Published">'],

            map(str, spec.states))

        # Transitions
        self.maxDiff = None
        self.assertEquals(
            ['<Transition "publish" ["Private" => "Published"]>',
             '<Transition "submit for publication" ["Private" => "Pending"]>',
             '<Transition "reject" ["Pending" => "Private"]>',
             '<Transition "retract" ["Pending" => "Private"]>',
             '<Transition "publish" ["Pending" => "Published"]>',
             '<Transition "reject" ["Published" => "Private"]>'],

            map(str, spec.transitions))

        # Role mappings
        self.assertEquals(
            ['<RoleMapping "editor-in-chief" => "Reviewer">',
             '<RoleMapping "editor" => "Editor">',
             '<RoleMapping "everyone" => "Anonymous">',
             '<RoleMapping "administrator" => "Site Administrator">'],

            map(str, spec.role_mappings))
