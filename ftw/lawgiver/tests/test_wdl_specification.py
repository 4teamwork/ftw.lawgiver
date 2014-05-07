from ftw.lawgiver.wdl.specification import Specification
from ftw.lawgiver.wdl.specification import Status
from ftw.lawgiver.wdl.specification import Transition
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

    def test_VALIDATION_no_initial_status(self):
        obj = Specification('My Workflow')
        with self.assertRaises(ValueError) as cm:
            obj.validate()

        self.assertEquals('No initial status defined.', str(cm.exception))

    def test_VALIDATION_unkown_initial_status(self):
        obj = Specification('My Workflow', initial_status_title='Foo')
        with self.assertRaises(ValueError) as cm:
            obj.validate()

        self.assertEquals('Definition of initial status "Foo" not found.',
                          str(cm.exception))

    def test_VALIDATION_visible_roles_must_be_in_role_mapping(self):
        obj = Specification('My Workflow',
                            initial_status_title='Private',
                            states={'Private': Status('Private', [])},
                            role_mapping={'editor-in-chief': 'Reviewer'},
                            visible_roles=['editor-in-chief', 'editor'])

        with self.assertRaises(ValueError) as cm:
            obj.validate()

        self.assertEquals('"editor" in visible roles is not in role mapping.',
                          str(cm.exception))

    def test_VALIDATION_role_description_must_validate_to_role_mapping(self):
        spec = Specification('My Workflow',
                             initial_status_title='Private',
                             states={'Private': Status('Private', [])},
                             role_mapping={'editor-in-chief': 'Reviewer'},
                             role_descriptions={'editor': 'Text'})

        with self.assertRaises(ValueError) as cm:
            spec.validate()

        self.assertEquals('"editor" in role description is not in role mapping.',
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

    def test_src_status_object_or_title_required(self):
        with self.assertRaises(ValueError) as cm:
            Transition('foo', dest_status_title='Bar')

        self.assertEquals('src_status or src_status_title required.',
                          str(cm.exception))

    def test_dest_status_object_or_title_required(self):
        with self.assertRaises(ValueError) as cm:
            Transition('foo', src_status_title='Bar')

        self.assertEquals('dest_status or dest_status_title required.',
                          str(cm.exception))

    def test_augmenting_states(self):
        obj = Transition('foo', src_status_title='Bar',
                         dest_status_title='Baz')

        states = {'Bar': Status('Bar', []),
                  'Baz': Status('Baz', [])}
        obj.augment_states(states)

        self.assertEquals(obj.src_status, states['Bar'])
        self.assertEquals(obj.dest_status, states['Baz'])

    def test_augmenting_missing_src_status(self):
        obj = Transition('foo', src_status_title='Bar',
                         dest_status_title='Baz')

        states = {'Baz': Status('Baz', [])}
        with self.assertRaises(ValueError) as cm:
            obj.augment_states(states)

        self.assertEquals('No such src_status "Bar" (foo).',
                          str(cm.exception))

    def test_augmenting_missing_dest_status(self):
        obj = Transition('foo', src_status_title='Bar',
                         dest_status_title='Baz')

        states = {'Bar': Status('Bar', [])}
        with self.assertRaises(ValueError) as cm:
            obj.augment_states(states)

        self.assertEquals('No such dest_status "Baz" (foo).',
                          str(cm.exception))
