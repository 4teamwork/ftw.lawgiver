from ftw.testbrowser import browser
from plone.app.testing import SITE_OWNER_NAME


def visit(obj):
    browser.login(SITE_OWNER_NAME)
    browser.open(obj, view='sharing')


def role_labels():
    return browser.css('#user-group-sharing-head th').text[1:]
