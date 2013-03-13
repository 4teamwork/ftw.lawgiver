from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from zope.configuration import xmlconfig


class LawmakerLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def setUpZope(self, app, configurationContext):

        import z3c.autoinclude
        xmlconfig.file('meta.zcml', z3c.autoinclude,
                       context=configurationContext)
        xmlconfig.string(
            '<configure xmlns="http://namespaces.zope.org/zope">'
            '  <includePlugins package="plone" />'
            '</configure>',
            context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'ftw.lawmaker:default')

LAWMAKER_FIXTURE = LawmakerLayer()
LAWMAKER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LAWMAKER_FIXTURE, ), name="ftw.lawmaker:integration")
LAWMAKER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(LAWMAKER_FIXTURE, ), name="ftw.lawmaker:functional")
