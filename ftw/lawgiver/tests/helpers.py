from ftw.testing import IS_PLONE_5
from path import Path
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import getFSVersionTuple
import os
import pkg_resources
import shlex
import subprocess
import transaction


ASSETS = Path(__file__).joinpath('..', 'assets').abspath()
PLONE_VERSION = getFSVersionTuple()

try:
    pkg_resources.get_distribution('collective.deletepermission')
except pkg_resources.DistributionNotFound:
    HAS_DELETEPERMISSION = False
else:
    HAS_DELETEPERMISSION = True


if PLONE_VERSION >= (5, 1, 0):
    if HAS_DELETEPERMISSION:
        EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-5.1.0-deletepermission')
    else:
        EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-5.1.0-no-deletepermission')
elif PLONE_VERSION >= (4, 3, 5):
    if HAS_DELETEPERMISSION:
        EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.3.5-deletepermission')
    else:
        EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.3.5-no-deletepermission')
else:
    EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.3.4')


EXAMPLE_WF_SPEC = EXAMPLE_WORKFLOW_DIR.joinpath('specification.txt')
EXAMPLE_WF_DEF = EXAMPLE_WORKFLOW_DIR.joinpath('definition.xml')


def filestructure_snapshot(path):
    paths = []
    for dirpath, _dirnames, filenames in os.walk(path):
        paths.append(dirpath)
        for filename in filenames:
            paths.append(os.path.join(dirpath, filename))

    return paths


def cleanup_path(path, snapshot_before):
    snapshot_after = filestructure_snapshot(path)
    to_delete = reversed(sorted(set(snapshot_after) - set(snapshot_before)))
    for path in to_delete:
        if os.path.isfile(path):
            os.unlink(path)
        if os.path.isdir(path):
            os.removedirs(path)


def run_command(cmd, cwd=None):
    proc = subprocess.Popen(shlex.split(cmd),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            cwd=cwd)

    stdout, stderr = proc.communicate()
    if proc.poll():
        raise Exception('Error while running "{0}":\n{1}'.format(
            cmd, stdout + stderr))


def switch_language(portal, lang_code):
    language_tool = getToolByName(portal, 'portal_languages')
    if IS_PLONE_5:
        language_tool.addSupportedLanguage(lang_code)
        language_tool.settings.use_combined_language_codes = False
        language_tool.setDefaultLanguage(lang_code)
    else:
        language_tool.manage_setLanguageSettings(
            lang_code,
            [lang_code],
            setUseCombinedLanguageCodes=False,
            startNeutral=False)
    transaction.commit()
