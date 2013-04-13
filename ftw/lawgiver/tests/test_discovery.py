from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from plone.app.testing import PloneSandboxLayer
from unittest2 import TestCase
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter
from zope.configuration import xmlconfig
from zope.interface.verify import verifyObject
import os


HERE = os.path.abspath(os.path.dirname(__file__)) + '/'


def make_path_relative(path):
    """Make paths relative to this directory.
    """
    assert path.startswith(HERE)
    return path[len(HERE):]


class SpecDiscoveryGSProfileLayer(PloneSandboxLayer):

    defaultBases = (LAWGIVER_INTEGRATION_TESTING, )

    def setUpZope(self, app, configurationContext):
        import ftw.lawgiver.tests
        xmlconfig.file('profiles/spec-discovery.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)


SPEC_DISCOVERY = SpecDiscoveryGSProfileLayer()


class TestWorkflowSpecificationDiscovery(TestCase):

    layer = SPEC_DISCOVERY

    def setUp(self):
        super(TestWorkflowSpecificationDiscovery, self).setUp()
        self.portal = self.layer['portal']

    def test_component_registered(self):
        component = queryMultiAdapter((self.portal, self.portal.REQUEST),
                                      IWorkflowSpecificationDiscovery)

        self.assertTrue(component,
                        'IWorkflowSpecificationDiscovery is not registered')

    def test_component_implements_interface(self):
        component = getMultiAdapter((self.portal, self.portal.REQUEST),
                                    IWorkflowSpecificationDiscovery)

        self.assertTrue(
            IWorkflowSpecificationDiscovery.providedBy(component))

        verifyObject(IWorkflowSpecificationDiscovery, component)

    def test_discover(self):
        # test based on "spec-discovery" test GS profile.

        component = getMultiAdapter((self.portal, self.portal.REQUEST),
                                    IWorkflowSpecificationDiscovery)

        result = map(make_path_relative, component.discover())

        prefix = 'profiles/spec-discovery/workflows/'
        self.assertEquals(
            set([prefix + 'spec-based-workflow/specification.txt',
                 prefix + 'another-spec-based-workflow/specification.txt',
                 prefix + 'invalid-spec/specification.txt']),
            set(result))

    def test_hash_unhash(self):
        # Do not test with an literal hash becuase it is based on the path
        # where the project is checked out - and therefore it may change.
        # That's why we test hash / unhash in combination.
        component = getMultiAdapter((self.portal, self.portal.REQUEST),
                                    IWorkflowSpecificationDiscovery)

        path = component.discover()[0]
        hash_ = component.hash(path)
        self.assertNotEquals(path, hash_, 'The hash should not be the path.')

        self.assertEquals(
            path, component.unhash(hash_),
            'Hashing and unhashing a path does not result in the same path.')

    def test_unhash_does_not_unhash_unkown_paths(self):
        # Unhashing unknown hashes would by a security issues, since an
        # intruder may make the parser parse files which were not meant to
        # be parsed.

        component = getMultiAdapter((self.portal, self.portal.REQUEST),
                                    IWorkflowSpecificationDiscovery)

        hash_ = component.hash('/tmp')
        self.assertEquals(
            None, component.unhash(hash_),
            'The unhashing method should not accept hashed paths which'
            ' are not registered as specification file.')
