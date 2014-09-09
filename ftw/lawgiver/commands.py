from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.updater import ConsoleMessageFormatter
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Testing.makerequest import makerequest
from zope.component import getUtility
from zope.component.hooks import setSite
import argparse
import sys


def discover_plone_site(app):
    for item_id, item in app.items():
        if IPloneSiteRoot.providedBy(item):
            return item_id
    return None


def load_site(app, path):
    if not path:
        print >>sys.stderr, 'ERROR: No Plone site found.' \
            ' Use --site or create a Plone site in the Zope app root.'
        sys.exit(1)

    app = makerequest(app)
    print 'Using site at: /{0}'.format(path)
    site = app.unrestrictedTraverse(path)
    app.REQUEST.PARENTS = [site, app]
    setSite(site)


def rebuild_workflows(app, instance_args):
    parser = argparse.ArgumentParser(
        description='Rebuild ftw.lawgiver workflows.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', help=argparse.SUPPRESS)  # swallows instance command

    parser.add_argument('-s', '--site', dest='site',
                        default=discover_plone_site(app),
                        help='Path to the Plone site for discovering the workflows.')

    args = parser.parse_args(instance_args)
    load_site(app, args.site)

    getUtility(IUpdater).update_all_specifications(
        output_formatter=ConsoleMessageFormatter())

    print 'DONE'
