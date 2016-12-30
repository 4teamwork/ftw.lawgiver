from path import Path
from Products.CMFPlone.utils import getFSVersionTuple
import os


ASSETS = Path(__file__).joinpath('..', 'assets').abspath()
PLONE_VERSION = getFSVersionTuple()


if PLONE_VERSION >= (4, 3, 5):
    EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.3.5')
elif PLONE_VERSION > (4, 3):
    EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.3.4')
else:
    EXAMPLE_WORKFLOW_DIR = ASSETS.joinpath('example-4.2')


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
