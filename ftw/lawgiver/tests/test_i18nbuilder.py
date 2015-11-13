# -*- coding: utf-8 -*-
from ftw.lawgiver.i18nbuilder import I18nBuilder
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.helpers import cleanup_path
from ftw.lawgiver.tests.helpers import filestructure_snapshot
from unittest2 import TestCase
import os
import re


I18N_ASSETS = os.path.join(os.path.dirname(__file__),
                           'assets', 'i18nbuilder')

POT_PATH = os.path.join(I18N_ASSETS, 'locales', 'plone.pot')

EN_PO_PATH = os.path.join(
    I18N_ASSETS, 'locales', 'en', 'LC_MESSAGES', 'plone.po')


SIMPLE_WORKFLOW_MESSAGES = r'''
#. Default: "Private"
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "Private"
msgstr "Private"

#. Default: "Published"
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "Published"
msgstr "Published"

#. Default: "püblish"
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "püblish"
msgstr "püblish"

#. Default: "editor"
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "simple_workflow--ROLE--Editor"
msgstr "editor"

#. Default: "An \"Editor\" writes articles."
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "simple_workflow--ROLE-DESCRIPTION--Editor"
msgstr "An \"Editor\" writes articles."
'''.strip()

OLD_SIMPLE_WORKFLOW_MESSAGES = r'''
#. Default: "No Longer Available"
#: ftw/lawgiver/tests/assets/i18nbuilder/profiles/default/workflows/simple_workflow/specification.txt
msgid "No Longer Available"
msgstr "No Longer Available"
'''


OTHER_MESSAGES = r'''
msgid "some-other-text"
msgstr "Some Other Text"
'''.strip()


PO_HEADER = r'''
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"POT-Creation-Date: YEAR-MO-DA HO:MI +ZONE\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI +ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=utf-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=1; plural=0\n"
"Preferred-Encodings: utf-8 latin1\n"
'''.strip()


class TestI18nBuilder(TestCase):
    layer = LAWGIVER_INTEGRATION_TESTING

    def setUp(self):
        self.simple_workflow_spec_path = os.path.join(
            I18N_ASSETS,
            'profiles', 'default', 'workflows',
            'simple_workflow', 'specification.txt')
        self.i18nassets_snapshot = filestructure_snapshot(I18N_ASSETS)

    def tearDown(self):
        cleanup_path(I18N_ASSETS, self.i18nassets_snapshot)

    def test_validates_path(self):
        with self.assertRaises(ValueError) as cm:
            I18nBuilder('/tmp/invalid/path/specification.txt')

        self.assertEquals('Path "/tmp/invalid/path/specification.txt"'
                          ' does not exist.',
                          str(cm.exception))

    def test_get_locales_directory(self):
        builder = I18nBuilder(self.simple_workflow_spec_path)
        locales_path = builder.get_locales_directory_path()
        self.assertEquals(os.path.join(I18N_ASSETS, 'locales'),
                          locales_path)

    def test_get_locales_directory_not_found_returns_None(self):
        asset_path = os.path.join(os.path.dirname(__file__),
                                  'assets', 'example.specification.txt')
        builder = I18nBuilder(asset_path)
        self.assertIsNone(builder.get_locales_directory_path(),
                          'There should no locales directory be found'
                          ' because "profiles" is not in the path.')

    def test_generate_pot_generates_pot_file(self):
        I18nBuilder(self.simple_workflow_spec_path).generate_pot()
        self.maxDiff = None
        self.assertMultiLineEqual(
            clear_msgstr(PO_HEADER + '\n\n' +
                         SIMPLE_WORKFLOW_MESSAGES + '\n'),
            read_file(POT_PATH))

    def test_generate_pot_updates_messages_and_keeps_existing(self):
        with open(POT_PATH, 'w+') as po_file:
            po_file.write(PO_HEADER)
            po_file.write('\n\n')
            po_file.write(clear_msgstr(OTHER_MESSAGES))

        I18nBuilder(self.simple_workflow_spec_path).generate_pot()

        self.maxDiff = None
        self.assertMultiLineEqual(
            clear_msgstr(PO_HEADER + '\n\n'
                         + SIMPLE_WORKFLOW_MESSAGES + '\n\n'
                         + OTHER_MESSAGES + '\n'),
            read_file(POT_PATH))

    def test_generate_pot_removes_old_messages_of_workflow(self):
        with open(POT_PATH, 'w+') as po_file:
            po_file.write(PO_HEADER)
            po_file.write('\n\n')
            po_file.write(clear_msgstr(OLD_SIMPLE_WORKFLOW_MESSAGES))

        I18nBuilder(self.simple_workflow_spec_path).generate_pot()

        self.maxDiff = None
        self.assertMultiLineEqual(
            clear_msgstr(PO_HEADER + '\n\n'
                         + SIMPLE_WORKFLOW_MESSAGES + '\n'),
            read_file(POT_PATH))

    def test_generate_po_generates_po_file(self):
        I18nBuilder(self.simple_workflow_spec_path).generate_po('en')
        self.maxDiff = None
        self.assertMultiLineEqual(
            PO_HEADER + '\n\n' +
            SIMPLE_WORKFLOW_MESSAGES + '\n',
            read_file(EN_PO_PATH))

    def test_generate_po_updates_messages_and_keeps_existing(self):
        os.makedirs(os.path.dirname(EN_PO_PATH))
        with open(EN_PO_PATH, 'w+') as po_file:
            po_file.write(PO_HEADER)
            po_file.write('\n\n')
            po_file.write(OTHER_MESSAGES)

        I18nBuilder(self.simple_workflow_spec_path).generate_po('en')

        self.maxDiff = None
        self.assertMultiLineEqual(
            PO_HEADER + '\n\n'
            + SIMPLE_WORKFLOW_MESSAGES + '\n\n'
            + OTHER_MESSAGES + '\n',
            read_file(EN_PO_PATH))

    def test_generate_po_removes_old_messages_of_workflow(self):
        os.makedirs(os.path.dirname(EN_PO_PATH))
        with open(EN_PO_PATH, 'w+') as po_file:
            po_file.write(PO_HEADER)
            po_file.write('\n\n')
            po_file.write(OLD_SIMPLE_WORKFLOW_MESSAGES)

        I18nBuilder(self.simple_workflow_spec_path).generate_po('en')
        I18nBuilder(self.simple_workflow_spec_path).generate_po('en')

        self.maxDiff = None
        self.assertMultiLineEqual(
            PO_HEADER + '\n\n'
            + SIMPLE_WORKFLOW_MESSAGES + '\n',
            read_file(EN_PO_PATH))

    def test_generate_generates_pot_and_po_files(self):
        self.assertFalse(os.path.exists(POT_PATH))
        self.assertFalse(os.path.exists(EN_PO_PATH))
        I18nBuilder(self.simple_workflow_spec_path).generate('en')
        self.assertTrue(os.path.exists(POT_PATH))
        self.assertTrue(os.path.exists(EN_PO_PATH))


def read_file(path):
    with open(path) as file_:
        return file_.read()


def clear_msgstr(text):
    return re.sub(r'msgstr ".*"$', 'msgstr ""', text, flags=re.M)
