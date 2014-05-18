from ftw.testing import browser
from ftw.testing.pages import Plone


class Sharing(Plone):

    def visit_on(self, obj):
        return self.visit(obj, '@@sharing')

    @property
    def role_labels(self):
        nodes = browser().find_by_css('#user-group-sharing-head th')
        return map(lambda node: node.text.strip(), nodes[1:])
