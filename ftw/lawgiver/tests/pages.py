from ftw.testing import browser
from ftw.testing.pages import Plone


class SpecsListing(Plone):

    def open(self):
        browser().visit('/'.join((self.portal_url, '@@lawgiver-list-specs')))
        assert self.get_template_class() == 'template-lawgiver-list-specs', \
            'Not on @@lawgiver-list-specs view!?: %s' % browser().url
