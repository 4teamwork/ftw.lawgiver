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



class TestSpecification(TestCase):

    def test_implements_interface(self):
        self.assertTrue(ISpecification.implementedBy(Specification))

        verifyClass(ISpecification, Specification)

    def test_string_repr(self):
        obj = Specification(title='My Workflow')
        self.assertEquals(unicode(obj),
                          u'<Specification "My Workflow">')


class TestStatus(TestCase):

    def test_implements_interface(self):
        self.assertTrue(IStatus.implementedBy(Status))

        verifyClass(IStatus, Status)

    def test_string_repr(self):
        obj = Status(title='Private', init=True)
        self.assertEquals(unicode(obj),
                          u'<Status "Private" [init]>')

        obj2 = Status(title='Public', init=False)
        self.assertEquals(unicode(obj2),
                          u'<Status "Public">')


class TestTransition(TestCase):

    def test_implements_interface(self):
        self.assertTrue(ITransition.implementedBy(Transition))

        verifyClass(ITransition, Transition)

    def test_string_repr(self):
        obj = Transition('publish', 'Private', 'Public')
        self.assertEquals(unicode(obj),
                          u'<Transition "publish" ["Private" => "Public"]>')

    def test_get_from_status_requires_augmentation(self):
        obj = Transition('publish', 'Private', 'Public')
        with self.assertRaises(RuntimeError) as cm:
            obj.get_from_status()

        self.assertEquals('augment() should be called first',
                          str(cm.exception))

    def test_get_to_status_requires_augmentation(self):
        obj = Transition('publish', 'Private', 'Public')
        with self.assertRaises(RuntimeError) as cm:
            obj.get_to_status()

        self.assertEquals('augment() should be called first',
                          str(cm.exception))


class TestRoleMapping(TestCase):

    def test_implements_interface(self):
        self.assertTrue(IRoleMapping.implementedBy(RoleMapping))

        verifyClass(IRoleMapping, RoleMapping)

    def test_string_repr(self):
        obj = RoleMapping('Secretary', 'Editor')
        self.assertEquals(unicode(obj),
                          u'<RoleMapping "Secretary" => "Editor">')
