from ftw.lawgiver.interfaces import IDynamicRoleAdapter
from ftw.lawgiver.testing import META_ZCML
from plone.app.workflow.interfaces import ISharingPageRole
from plone.mocktestcase.dummy import Dummy
from unittest2 import TestCase
from zope.component import getSiteManager
from zope.component import queryMultiAdapter
from zope.component import queryUtility
from zope.component.hooks import setSite


class TestRoleDirective(TestCase):

    layer = META_ZCML

    def setUp(self):
        site = Dummy(REQUEST=Dummy(PARENTS=[None]),
                     getSiteManager=getSiteManager)
        setSite(site)

    def tearDown(self):
        setSite(None)

    def test_directive_registers_role_utility(self):
        self.assertEquals(
            None, queryUtility(ISharingPageRole, name='Integrator'),
            'Unexpectly found role utility "Integrator" before registering.')

        self.load_zcml(
            '<lawgiver:role',
            '    name="Integrator"',
            '    />')

        role_utility = queryUtility(ISharingPageRole, name='Integrator')
        self.assertTrue(role_utility, 'Role utility was not registered')
        self.assertTrue(ISharingPageRole.providedBy(role_utility),
                        'Role utility does not implement ISharingPageRole')

    def test_directive_registers_role_adapter(self):
        self.assertEquals(
            None, queryMultiAdapter((None, None), IDynamicRoleAdapter,
                                    name='Integrator'),
            'Unexpectly found role adapter "Integrator" before registering.')

        self.load_zcml(
            '<lawgiver:role',
            '    name="Integrator"',
            '    />')

        role_adapter = queryMultiAdapter((None, None), IDynamicRoleAdapter,
                                         name='Integrator')
        self.assertTrue(role_adapter, 'Role adapter was not registered')
        self.assertTrue(IDynamicRoleAdapter.providedBy(role_adapter),
                        'Role adapter does not implement IDynamicRoleAdapter')

    def test_required_permission_is_set_properly(self):
        permission = 'Sharing page: Delegate Integrator role'

        self.load_zcml(
            '<lawgiver:role',
            '    name="Integrator"',
            '    permission="%s"' % permission,
            '    />')

        role_utility = queryUtility(ISharingPageRole, name='Integrator')
        self.assertEquals(permission, role_utility.required_permission)

    def test_default_permission_is_set_properly(self):
        self.load_zcml(
            '<lawgiver:role',
            '    name="Integrator"',
            '    />')

        role_utility = queryUtility(ISharingPageRole, name='Integrator')
        self.assertEquals('Sharing page: Delegate Integrator role',
                          role_utility.required_permission)

    def load_zcml(self, *lines):
        lines = list(lines)
        lines.insert(0,
                     '<configure \n'
                     'package="ftw.lawgiver" '
                     'xmlns:lawgiver="http://namespaces.zope.org/lawgiver" \n'
                     'i18n_domain="ftw.lawgiver">')
        lines.append('</configure>')
        self.layer.load_zcml_string('\n'.join(lines))
