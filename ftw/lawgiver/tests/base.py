from StringIO import StringIO
from ftw.testing import MockTestCase
from lxml import etree


CONFIGURE = '''
<configure xmlns:lawgiver="http://namespaces.zope.org/lawgiver">
%s
</configure>
'''


class BaseTest(MockTestCase):

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
        self.layer.load_zcml_string(
            '<configure xmlns="http://namespaces.zope.org/zope"'
            '           i18n_domain="foo">%s'
            '</configure>' % '\n'.join(
                map(lambda item: '<permission id="%s" title="%s"/>' % item,
                    kwargs.items())))

    def _canonicalize_xml(self, text):
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
        xml.getroottree().write_c14n(norm)
        xml = etree.fromstring(norm.getvalue())
        return etree.tostring(xml.getroottree(), pretty_print=True,
                              xml_declaration=True,
                              encoding='utf-8')

    def assert_xml(self, xml1, xml2):
        norm1 = self._canonicalize_xml(xml1)
        norm2 = self._canonicalize_xml(xml2)
        self.maxDiff = None
        self.assertMultiLineEqual(norm1, norm2)
