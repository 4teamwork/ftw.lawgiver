from ftw.testbrowser import browser
from functools import partial
from operator import methodcaller
from plone.app.testing import SITE_OWNER_NAME
import os.path


TESTS_DIRECTORY = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..'))


def visit(specification_title):
    browser.login(SITE_OWNER_NAME)
    browser.open(view='lawgiver-list-specs')
    specs = browser.css('dl.specifications').first
    link = specs.find(specification_title)
    assert link, 'Spec {!r} not found in {!r}'.format(
        specification_title, specs.terms)
    link.click()


def metadata():
    replace_path_in_row = partial(map, methodcaller('replace',
                                                    TESTS_DIRECTORY, '....'))
    return map(replace_path_in_row,
               browser.css('table.spec-metadata').first.lists())


def specification_text():
    return browser.css('dl.specification dd pre').first.text


def action_groups():
    return dict(map(lambda action_group: (action_group[0].text,
                                          action_group[1].css('li').text),
                    browser.css('dl.permission-mapping dd dl').first.items()))

def unmanaged_permissions():
    return browser.css('dl.unmanaged-permissions dd li').text


def translations_pot():
    return browser.css('dl.translations dd pre.pot').first.raw_text.strip()


def translations_po():
    return browser.css('dl.translations dd pre.po').first.raw_text.strip()


def button_write():
    return browser.find('Write workflow definition')


def button_write_and_import():
    return browser.find('Write and Import Workflow')


def button_reindex():
    return browser.find('Update security settings')


def button_update_locales():
    return browser.find('Update translations in locales directory')
