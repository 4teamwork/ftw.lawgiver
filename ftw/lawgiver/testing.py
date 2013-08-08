from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing import ComponentRegistryLayer
from ftw.testing import FunctionalSplinterTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from zope.configuration import xmlconfig


class MetaZCMLLayer(ComponentRegistryLayer):

    def setUp(self):
        super(MetaZCMLLayer, self).setUp()

        import ftw.lawgiver
        self.load_zcml_file('meta.zcml', ftw.lawgiver)


META_ZCML = MetaZCMLLayer()


class ZCMLLayer(ComponentRegistryLayer):

    def setUp(self):
        super(ZCMLLayer, self).setUp()

        import ftw.lawgiver.tests
        self.load_zcml_file('tests.zcml', ftw.lawgiver.tests)


ZCML_FIXTURE = ZCMLLayer()


class LawgiverLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, BUILDER_LAYER)

    def setUpZope(self, app, configurationContext):
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.lawgiver:default')

LAWGIVER_FIXTURE = LawgiverLayer()
LAWGIVER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LAWGIVER_FIXTURE, ), name="ftw.lawgiver:integration")
LAWGIVER_FUNCTIONAL_TESTING = FunctionalSplinterTesting(
    bases=(LAWGIVER_FIXTURE,
           set_builder_session_factory(functional_session_factory)),
    name="ftw.lawgiver:functional")


class TestingSpecificationsLayer(PloneSandboxLayer):

    defaultBases = (LAWGIVER_FUNCTIONAL_TESTING, )

    def setUpZope(self, app, configurationContext):
        import ftw.lawgiver.tests

        xmlconfig.file('profiles/spec-discovery.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('profiles/custom-workflow.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('profiles/foo.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('profiles/bar.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('profiles/destructive.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)

        xmlconfig.file('profiles/role-translation.zcml',
                       ftw.lawgiver.tests,
                       context=configurationContext)


SPECIFICATIONS_FUNCTIONAL = TestingSpecificationsLayer()
