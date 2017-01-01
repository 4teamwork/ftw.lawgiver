from ftw.builder.testing import BUILDER_LAYER
from ftw.builder.testing import functional_session_factory
from ftw.builder.testing import set_builder_session_factory
from ftw.testing import ComponentRegistryLayer
from ftw.testing.layer import COMPONENT_REGISTRY_ISOLATION
from ftw.testing.layer import TEMP_DIRECTORY
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.testing import z2
from zope.configuration import xmlconfig
import ftw.lawgiver.tests.builders


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

    defaultBases = (COMPONENT_REGISTRY_ISOLATION, BUILDER_LAYER, TEMP_DIRECTORY)

    def setUpZope(self, app, configurationContext):
        # The first definition of an action group defines the the
        # translation domain - and we cant control ZCML load order.
        # ftw.lawgiver needs to make sure that the default action groups are
        # translated in the ftw.lawgiver domain at least as fallback.
        # For producing this error we add an action group before loading
        # our ZCML.
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope"'
            '           xmlns:lawgiver="http://namespaces.zope.org/lawgiver"'
            '           xmlns:i18n="http://namespaces.zope.org/i18n"'
            '           i18n_domain="ftw.contentpage">'
            '  <include package="ftw.lawgiver" file="meta.zcml" />'
            '  <lawgiver:map_permissions'
            '      action_group="add"'
            '      permissions="Add some type" />'
            '</configure>',
            context=configurationContext)

        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <include package="z3c.autoinclude" file="meta.zcml" />'
            '  <includePlugins package="plone" />'
            '  <includePluginsOverrides package="plone" />'
            '</configure>',
            context=configurationContext)

        # For making sure that having the same permission in multiple action groups
        # does not break the workflow building, we just create a new action group
        # with permissions already mapped to "add".
        # When this breaks the "add" action group, we'd notice it in the example
        # workflow test.
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope"'
            '           xmlns:lawgiver="http://namespaces.zope.org/lawgiver">'
            '  <lawgiver:map_permissions'
            '      action_group="add folders"'
            '      permissions="Add portal content,'
            '                   ATContentTypes: Add Folder"'
            '      move="False"'
            '      />'
            '</configure>',
            context=configurationContext)

        z2.installProduct(app, 'ftw.lawgiver')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.lawgiver:default')

LAWGIVER_FIXTURE = LawgiverLayer()
LAWGIVER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LAWGIVER_FIXTURE, ), name="ftw.lawgiver:integration")
LAWGIVER_FUNCTIONAL_TESTING = FunctionalTesting(
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
