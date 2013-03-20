from ftw.testing import browser
from ftw.testing.pages import Plone


class SpecItem(object):

    def __init__(self, dtnode, ddnode):
        self.dtnode = dtnode
        self.ddnode = ddnode

    def link_text(self):
        return self.dtnode.find_by_xpath('a').text

    def link_href(self):
        return self.dtnode.find_by_xpath('a')['href']

    def description(self):
        return self.ddnode.text

    def click(self):
        self.dtnode.find_by_xpath('a').click()

    def __repr__(self):
        return '<SpecItem "%s">' % self.link_text()


class SpecsListing(Plone):

    def open(self):
        browser().visit('/'.join((self.portal_url, '@@lawgiver-list-specs')))
        assert self.get_template_class() == 'template-lawgiver-list-specs', \
            'Not on @@lawgiver-list-specs view!?: %s' % browser().url

    def get_specifications(self):
        result = []

        for dtnode in browser().find_by_xpath(
            '//dl[@class="specifications"]/dt'):

            ddnode = dtnode.find_by_xpath('following-sibling::*[self::dd]')
            result.append(SpecItem(dtnode, ddnode))

        return result

    def get_specification_by_text(self, text):
        for spec in self.get_specifications():
            if spec.link_text() == text:
                return spec

        raise KeyError('Specification link with text "%s" not found' % text)
