from ftw.lawgiver.wdl.interfaces import IRoleMapping
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IStatus
from ftw.lawgiver.wdl.interfaces import ISyntaxTreeElement
from ftw.lawgiver.wdl.interfaces import ITransition
from ftw.lawgiver.wdl.utils import get_line_number
from operator import methodcaller
from zope.interface import implements
from zope.schema.interfaces import ConstraintNotSatisfied


class BaseSyntaxTreeElement(object):
    implements(ISyntaxTreeElement)

    def recursive_collect_objects(self, collection):
        collection.add(self)

    def validate(self, specification, warnings):
        pass

    def augment(self, specification):
        pass


class Specification(BaseSyntaxTreeElement):
    implements(ISpecification)

    def __init__(self, title, description=None,
                 states=None, transitions=None, role_mappings=None):
        self.title = title
        self.description = description
        self.states = states or []
        self.transitions = transitions or []
        self.role_mappings = role_mappings or []

    def get_status_by_title(self, title):
        for status in self.states:
            if status.title == title:
                return status
        return None

    def __repr__(self):
        return u'<Specification "%s">' % self.title

    def recursive_collect_objects(self, collection):
        collection.add(self)

        recurse = methodcaller('recursive_collect_objects', collection)
        map(recurse, self.states)
        map(recurse, self.transitions)
        map(recurse, self.role_mappings)


class Status(BaseSyntaxTreeElement):
    implements(IStatus)

    def __init__(self, title, init=False):
        self.title = title
        self.init_status = init

    def __repr__(self):
        return u'<Status "%s"%s>' % (
            self.title,
            self.init_status and ' [init]' or '')


class Transition(BaseSyntaxTreeElement):
    implements(ITransition)

    def __init__(self, title, from_status, to_status):
        self.title = title
        self.from_status_title = from_status
        self.to_status_title = to_status
        self.from_status = None
        self.to_status = None

    def get_from_status(self):
        if self.from_status is None:
            raise RuntimeError('augment() should be called first')
        return self.from_status

    def get_to_status(self):
        if self.to_status is None:
            raise RuntimeError('augment() should be called first')
        return self.to_status

    def __repr__(self):
        return u'<Transition "%s" ["%s" => "%s"]>' % (
            self.title,
            self.from_status_title,
            self.to_status_title)

    def validate(self, specification, warnings):
        if not specification.get_status_by_title(self.from_status_title):
            raise ConstraintNotSatisfied(
                'There is no status with title "%s". (Line %s)' % (
                    self.from_status_title, get_line_number(self)))

        if not specification.get_status_by_title(self.to_status_title):
            raise ConstraintNotSatisfied(
                'There is no status with title "%s". (Line %s)' % (
                    self.to_status_title, get_line_number(self)))

    def augment(self, specification):
        self.from_status = specification.get_status_by_title(
            self.from_status_title)

        self.to_status = specification.get_status_by_title(
            self.to_status_title)


class RoleMapping(BaseSyntaxTreeElement):
    implements(IRoleMapping)

    def __init__(self, customer_role, plone_role):
        self.customer_role = customer_role
        self.plone_role = plone_role

    def __repr__(self):
        return u'<RoleMapping "%s" => "%s">' % (
            self.customer_role,
            self.plone_role)
