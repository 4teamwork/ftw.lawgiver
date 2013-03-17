from ftw.lawgiver.wdl.interfaces import IRoleMapping
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IStatus
from ftw.lawgiver.wdl.interfaces import ITransition
from zope.interface import implements
from zope.schema.interfaces import ConstraintNotSatisfied



class Specification(object):
    implements(ISpecification)

    def __init__(self, title, description=None,
                 states=None, initial_status_title=None,
                 transitions=None, role_mappings=None):
        self.title = title
        self.description = description
        self._initial_status_title = initial_status_title
        self.states = states or []
        self.transitions = transitions or []
        self.role_mappings = role_mappings or []

    def __repr__(self):
        return u'<Specification "%s">' % self.title

    def get_initial_status(self):
        for status in self.states:
            if status.title == self._initial_status_title:
                return status
        return None

    def validate(self):
        if not self._initial_status_title:
            raise ConstraintNotSatisfied('No initial status defined.')

        if not self.get_initial_status():
            raise ConstraintNotSatisfied(
                'Definition of initial status "%s" not found.' % (
                    self._initial_status_title))


class Status(object):
    implements(IStatus)

    def __init__(self, title, statements):
        self.title = title
        self.statements = statements

    def __repr__(self):
        return u'<Status "%s">' % self.title


class Transition(object):
    implements(ITransition)

    def __init__(self, title, src_status, dest_status):
        self.title = title
        self.src_status = src_status
        self.dest_status = dest_status

    def __repr__(self):
        return u'<Transition "%s" ["%s" => "%s"]>' % (
            self.title,
            self.src_status.title,
            self.dest_status.title)


class RoleMapping(object):
    implements(IRoleMapping)

    def __init__(self, customer_role, plone_role):
        self.customer_role = customer_role
        self.plone_role = plone_role

    def __repr__(self):
        return u'<RoleMapping "%s" => "%s">' % (
            self.customer_role,
            self.plone_role)
