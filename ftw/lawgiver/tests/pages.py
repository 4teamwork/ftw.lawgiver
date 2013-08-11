from ftw.testing import browser
from ftw.testing.pages import Plone
from operator import attrgetter


class SpecItem(object):

    def __init__(self, dtnode, ddnode):
        self.dtnode = dtnode
        self.ddnode = ddnode

    def link_text(self):
        return self.dtnode.find_by_xpath('a').text

    def link_href(self):
        return self.dtnode.find_by_xpath('a').first['href']

    def description(self):
        return self.ddnode.text

    def click(self):
        browser().find_link_by_text(self.link_text()).click()

    def __repr__(self):
        return '<SpecItem "%s">' % self.link_text()


class SpecsListing(Plone):

    def open(self):
        browser().visit(self.listing_url)
        assert self.get_template_class() == 'template-lawgiver-list-specs', \
            'Not on @@lawgiver-list-specs view!?: %s' % browser().url

    @property
    def listing_url(self):
        return '/'.join((self.portal_url, '@@lawgiver-list-specs'))

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


class SpecDetails(Plone):

    def open(self, workflow_label):
        """Opens the workflow specification details view for a workflow.
        The passed workflow label is of the format "title (id)" if the
        specification can be parsed, otherwise just the title.
        """
        SpecsListing().open()
        SpecsListing().get_specification_by_text(workflow_label).click()
        self.assert_body_class('template-lawgiver-spec-details')

    def get_spec_metadata_table(self):
        data = []

        for row in browser().find_by_css('table.spec-metadata tr'):
            th = row.find_by_xpath('th').first
            td = row.find_by_xpath('td').first
            data.append((self.normalize_whitespace(th.text),
                         self.normalize_whitespace(td.text)))

        return data

    def is_workflow_installed(self):
        metadata = dict(self.get_spec_metadata_table())
        value = metadata['Workflow installed:']
        assert value in ('Yes', 'No'), \
            'Unkown "Workflow installed:" value: %s' % str(value)

        return value == 'Yes'


    def get_specification_text(self):
        return browser().find_by_css('dl.specification dd pre').first.text

    def get_specification_mapping(self):
        mapping = {}

        groups = browser().find_by_css('dl.permission-mapping dd dl dt')
        for actiongroup in groups:
            groupname = actiongroup.text

            permissionlist = actiongroup.find_by_xpath(
                'following-sibling::*[self::dd]').first

            permissions = map(attrgetter('text'),
                              permissionlist.find_by_css('li'))
            mapping[groupname] = permissions

        return mapping

    def get_unmanaged_permissions(self):
        return map(attrgetter('text'),
                   browser().find_by_css('dl.unmanaged-permissions dd li'))

    def get_translations_pot(self):
        return browser().find_by_css('dl.translations dd pre.pot').first.text

    def get_translations_po(self):
        return browser().find_by_css('dl.translations dd pre.po').first.text

    def button_write(self):
        return self.get_button('Write workflow definition')

    def button_write_and_import(self):
        return self.get_button('Write and Import Workflow')

    def button_reindex(self):
        return self.get_button('Update security settings')

class SpecDetailsConfirmation(SpecDetails):

    def is_confirmation_dialog_opened(self):
        return len(browser().find_by_css('.confirmation-message')) > 0

    def get_confirmation_dialog_text(self):
        return self.normalize_whitespace(
            browser().find_by_css('.confirmation-message').first.text)

    def confirm(self):
        self.click_button("I know what I am doing")

    def cancel(self):
        self.click_button("I am on production")


class Sharing(Plone):

    def visit_on(self, obj):
        return self.visit(obj, '@@sharing')

    @property
    def role_labels(self):
        nodes = browser().find_by_css('#user-group-sharing-head th')
        return map(lambda node: node.text.strip(), nodes[1:])
