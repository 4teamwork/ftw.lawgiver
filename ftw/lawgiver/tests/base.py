from StringIO import StringIO
from ftw.testing import MockTestCase
from lxml import etree
from zope.component import getSiteManager
from zope.component.hooks import getSite
from zope.component.hooks import setSite


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


class BaseTest(MockTestCase):

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
