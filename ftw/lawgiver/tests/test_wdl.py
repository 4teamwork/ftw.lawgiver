from StringIO import StringIO
from ftw.lawgiver.testing import WDL_ZCML
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from unittest2 import TestCase
from zope.component import getUtility


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

        # XXX test states
        self.assertEquals(forward.title, 'forward')
        self.assertEquals(backward.title, 'backward')

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
