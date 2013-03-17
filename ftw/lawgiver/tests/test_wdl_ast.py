from ftw.lawgiver.wdl.ast import RoleMapping
from ftw.lawgiver.wdl.ast import Specification
from ftw.lawgiver.wdl.ast import Status
from ftw.lawgiver.wdl.ast import Transition
from ftw.lawgiver.wdl.interfaces import IRoleMapping
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IStatus
from ftw.lawgiver.wdl.interfaces import ITransition
from unittest2 import TestCase
from zope.interface.verify import verifyClass
from zope.schema.interfaces import ConstraintNotSatisfied



class TestSpecification(TestCase):

    def test_implements_interface(self):
        self.assertTrue(ISpecification.implementedBy(Specification))

        verifyClass(ISpecification, Specification)

    def test_string_repr(self):
        obj = Specification(title='My Workflow')
        self.assertEquals(unicode(obj),
                          u'<Specification "My Workflow">')

    def test_VALIDATION_no_initial_status(self):
        obj = Specification('My Workflow')
        with self.assertRaises(ConstraintNotSatisfied) as cm:
            obj.validate()

        self.assertEquals('No initial status defined.', str(cm.exception))

    def test_VALIDATION_unkown_initial_status(self):
        obj = Specification('My Workflow', initial_status_title='Foo')
        with self.assertRaises(ConstraintNotSatisfied) as cm:
            obj.validate()

        self.assertEquals('Definition of initial status "Foo" not found.',
                          str(cm.exception))


class TestStatus(TestCase):

    def test_implements_interface(self):
        self.assertTrue(IStatus.implementedBy(Status))

        verifyClass(IStatus, Status)

    def test_string_repr(self):
        obj = Status('Private', [])
        self.assertEquals(unicode(obj),
                          u'<Status "Private">')


class TestTransition(TestCase):

    def test_implements_interface(self):
        self.assertTrue(ITransition.implementedBy(Transition))

        verifyClass(ITransition, Transition)

    def test_string_repr(self):
        private = Status('Private', [])
        public = Status('Public', [])
        obj = Transition('publish', private, public)
        self.assertEquals(unicode(obj),
                          u'<Transition "publish" ["Private" => "Public"]>')


class TestRoleMapping(TestCase):

    def test_implements_interface(self):
        self.assertTrue(IRoleMapping.implementedBy(RoleMapping))

        verifyClass(IRoleMapping, RoleMapping)

    def test_string_repr(self):
        obj = RoleMapping('Secretary', 'Editor')
        self.assertEquals(unicode(obj),
                          u'<RoleMapping "Secretary" => "Editor">')
