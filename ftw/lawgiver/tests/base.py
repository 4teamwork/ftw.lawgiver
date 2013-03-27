from StringIO import StringIO
from ftw.lawgiver.interfaces import IActionGroupRegistry
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
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
<configure xmlns:lawgiver="http://namespaces.zope.org/lawgiver">
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

    def map_permissions(self, permissions, action_group, workflow_name=None):
        self.load_map_permissions_zcml(
            '<lawgiver:map_permissions',
            '    action_group="%s"' % action_group,
            '    permissions="%s"' % ','.join(permissions),
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

    def get_name(self):
        return os.path.basename(self.workflow_path)

    def _is_base_test(self):
        """Detect that the class was not subclassed so we can skip the tests.
        """
        return type(self) == WorkflowTest

    def test_workflow_path(self):
        if self._is_base_test():
            return

        spec = self.get_path('specification.txt')
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

        with open(self.get_path('specification.txt')) as spec_file:
            spec = parser(spec_file)

        with open(self.get_path('result.xml'), 'w+') as result_file:
            generator = getUtility(IWorkflowGenerator)
            generator(self.get_name(), spec, result_file)
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

        # We use the the workflow_name __unmanaged__ since the permissions
        # we do not want to manage by default are registered on this fake
        # workflow so that we can track whether we are not managing them
        # by intention.

        for item in self.layer['portal'].ac_inherited_permissions(1):
            permission = item[0]

            if ',' in permission:
                # permissions with commas in the title are not supported
                # because it conflicts with the comma separated ZCML.
                # e.g. "Public, everyone can access"
                continue

            if not registry.get_action_group_for_permission(
                permission, workflow_name='__unmanaged__'):

                unmapped.append(permission)

        self.maxDiff = None
        self.assertEquals(
            [], unmapped,
            'There are default Plone permissions which are not yet mapped'
            ' to action groups.')
