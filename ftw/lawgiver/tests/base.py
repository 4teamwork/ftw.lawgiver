from StringIO import StringIO
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.lawgiver.wdl.languages import LANGUAGES
from ftw.testing import MockTestCase
from lxml import etree
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.component.hooks import setSite
from zope.dottedname.resolve import resolve
import os
import unittest2


CONFIGURE = '''
<configure xmlns:lawgiver="http://namespaces.zope.org/lawgiver" i18n_domain="ftw.lawgiver">
%s
</configure>
'''


def definition_xml_eliminate_standalone(node):
    if node.text is not None or len(node) > 0:
        return
    node.text = '\n  '


def definition_xml_node_sorter(nodea, nodeb):
    definition_xml_eliminate_standalone(nodea)
    definition_xml_eliminate_standalone(nodeb)

    if nodea.tag != nodeb.tag:
        return cmp(nodea.tag, nodeb.tag)

    elif nodea.tag in ('permission', 'permission-role', 'guard-role'):
        return cmp(nodea.text, nodeb.text)

    elif nodea.tag == 'state':
        return cmp(nodea.get('state_id'),
                   nodeb.get('state_id'))

    elif nodea.tag in ('transition', 'exit-transition'):
        return cmp(nodea.get('transition_id'),
                   nodeb.get('transition_id'))

    return 0


class FakeSite(object):

    def __init__(self):
        self._permissions = []

    def register_permission(self, name):
        self._permissions.append((name, ))

    def ac_inherited_permissions(self, all=0):
        if all:
            return self._permissions
        else:
            # When all=0 on a real site the result is reduced.
            # We do not want that in any situation, therefore we let the
            # tests fail when all=0 for detecting this.
            return []

    getSiteManager = getSiteManager


class XMLDiffTestCase(unittest2.TestCase):

    def _canonicalize_xml(self, text, node_sorter=None):
        parser = etree.XMLParser(remove_blank_text=True)
        try:
            xml = etree.fromstring(text, parser)
        except etree.XMLSyntaxError, exc:
            print '-' * 10
            print exc.error_log
            print '-' * 10
            print text
            print '-' * 10
            raise

        norm = StringIO()
        if node_sorter:
            # Search for parent elements
            for parent in xml.xpath('//*[./*]'):
                parent[:] = sorted(parent, node_sorter)

        xml.getroottree().write_c14n(norm)
        xml = etree.fromstring(norm.getvalue())
        return etree.tostring(xml.getroottree(),
                              pretty_print=True,
                              xml_declaration=True,
                              encoding='utf-8')

    def assert_xml(self, xml1, xml2):
        norm1 = self._canonicalize_xml(xml1)
        norm2 = self._canonicalize_xml(xml2)
        self.maxDiff = None
        self.assertMultiLineEqual(norm1, norm2)

    def assert_definition_xmls(self, xml1, xml2):
        norm1 = self._canonicalize_xml(
            xml1, node_sorter=definition_xml_node_sorter)
        norm2 = self._canonicalize_xml(
            xml2, node_sorter=definition_xml_node_sorter)
        self.maxDiff = None
        self.assertMultiLineEqual(norm1, norm2)


class BaseTest(MockTestCase, XMLDiffTestCase):

    def setUp(self):
        super(BaseTest, self).setUp()
        site = FakeSite()
        setSite(site)

    def map_permissions(self, permissions, action_group, workflow_name=None, move=True):
        self.load_map_permissions_zcml(
            '<lawgiver:map_permissions',
            '    action_group="%s"' % action_group,
            '    permissions="%s"' % ','.join(permissions),
            '    move="%s"' % str(move),
            '    %s />' % (
                workflow_name and 'workflow="%s"' % workflow_name or ''))

    def load_map_permissions_zcml(self, *lines):
        zcml = CONFIGURE % '\n'.join(lines)
        self.layer.load_zcml_string(zcml)

    def register_permissions(self, **kwargs):
        site = getSite()
        if site is None:
            site = FakeSite()
            setSite(site)
        else:
            assert isinstance(site, FakeSite), \
                'There is already a site (getSite) which is not FakeSite -' +\
                ' using register_permissions does not work..'

        for id_, name in kwargs.items():
            site.register_permission(name)


class EqualityTestCase(XMLDiffTestCase):

    def test_equality(self):
        if self._is_base_test():
            return

        assert getattr(self, 'specifications', None), \
            'Setup of %s wrong: no specifications defined (equality test)' % (
            type(self).__name__)

        definitions = {}

        for path in self.specifications:
            spec = self.get_spec(path)
            definitions[path] = StringIO()
            self.generate_workflow(spec, definitions[path])

        pairs = []
        reduce(lambda a, b: pairs.append((a, b)) or b, definitions)

        for name_a, name_b in pairs:
            locals()['__traceback_info__'] = name_a, name_b
            self.assert_definition_xmls(
                definitions[name_a].getvalue(),
                definitions[name_b].getvalue())

    def generate_workflow(self, spec, result):
        name = type(self).__name__
        generator = getUtility(IWorkflowGenerator)
        generator(name, spec).write(result)
        result.seek(0)

    def get_spec(self, path):
        parser = getUtility(IWorkflowSpecificationParser)

        with open(self.get_absolute_path(path)) as spec_file:
            return parser(spec_file, path=path)

    def get_absolute_path(self, path):
        if path.startswith('/'):
            return path

        else:
            return os.path.join(
                    os.path.dirname(resolve(self.__module__).__file__),
                    path)

    def _is_base_test(self):
        """Detect that the class was not subclassed so we can skip the tests.
        """
        return type(self) == EqualityTestCase


class WorkflowTest(XMLDiffTestCase):

    workflow_path = None

    def get_path(self, filename):
        self.assertIsNotNone(self.workflow_path,
                             'No workflow_path defined.'
                             ' Should be the relative path to the'
                             ' workflow directory.')

        if self.workflow_path.startswith('/'):
            return os.path.join(
                self.workflow_path,
                filename)

        else:
            return os.path.join(
                    os.path.dirname(resolve(self.__module__).__file__),
                    self.workflow_path,
                    filename)

    def get_specification_path(self):
        for language in LANGUAGES.values():
            path = self.get_path(language.filename)
            if os.path.exists(path):
                return path
        return self.get_path('specification.txt')

    def get_name(self):
        return os.path.basename(self.workflow_path)

    def _is_base_test(self):
        """Detect that the class was not subclassed so we can skip the tests.
        """
        return type(self) == WorkflowTest

    def test_workflow_path(self):
        if self._is_base_test():
            return

        spec = self.get_specification_path()
        self.assertTrue(os.path.exists(spec), 'No such file %s' % spec)
        spec = self.get_path('definition.xml')
        self.assertTrue(os.path.exists(spec), 'No such file %s' % spec)

    def test_layer(self):
        if self._is_base_test():
            return

        self.assertIsNotNone(
            getattr(self, 'layer', None),
            'No testing layer defined for %s -'
            ' should be an integration layer.' % type(self).__name__)

    def test_workflow_definition_up_to_date(self):
        if self._is_base_test():
            return

        parser = getUtility(IWorkflowSpecificationParser)

        path = self.get_specification_path()
        with open(path) as spec_file:
            spec = parser(spec_file, path=path)

        with open(self.get_path('result.xml'), 'w+') as result_file:
            generator = getUtility(IWorkflowGenerator)
            generator(self.get_name(), spec).write(result_file)
            result_file.seek(0)
            result = result_file.read()

        with open(self.get_path('definition.xml')) as expected_file:
            self.assert_definition_xmls(
                expected_file.read(), result)

    def test_no_unmapped_permissions(self):
        if self._is_base_test():
            return

        unmapped = []
        registry = getUtility(IActionGroupRegistry)

        explicitly_ignored_permissions = registry.get_ignored_permissions(
            workflow_name=self.get_name())

        for item in self.layer['portal'].ac_inherited_permissions(1):
            permission = item[0]

            if ',' in permission:
                # permissions with commas in the title are not supported
                # because it conflicts with the comma separated ZCML.
                # e.g. "Public, everyone can access"
                continue

            if registry.get_action_groups_for_permission(
                permission, workflow_name=self.get_name()):
                continue

            if permission not in explicitly_ignored_permissions:
                unmapped.append(permission)

        self.maxDiff = None
        self.assertEquals(
            [], unmapped,
            'There are permissions which are not yet mapped'
            ' to action groups, nor marked as not to manage.')
