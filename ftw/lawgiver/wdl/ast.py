from ftw.lawgiver.wdl.interfaces import IRoleMapping
from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IStatus
from ftw.lawgiver.wdl.interfaces import ITransition
from zope.interface import implements


class Specification(object):
    implements(ISpecification)

    def __init__(self, title, description=None,
                 states=None, transitions=None, role_mappings=None):
        self.title = title
        self.description = description
        self.states = states or []
        self.transitions = transitions or []
        self.role_mappings = role_mappings or []

    def __repr__(self):
        return u'<Specification "%s">' % self.title


class Status(object):
    implements(IStatus)

    def __init__(self, title, init=False):
        self.title = title
        self.init_status = init

    def __repr__(self):
        return u'<Status "%s"%s>' % (
            self.title,
            self.init_status and ' [init]' or '')


class Transition(object):
    implements(ITransition)

    def __init__(self, title, from_status, to_status):
        self.title = title
        self.from_status_title = from_status
        self.to_status_title = to_status

    def get_from_status(self):
        # XXX implement
        raise NotImplementedError()

    def get_to_status(self):
        # XXX implement
        raise NotImplementedError()

    def __repr__(self):
        return u'<Transition "%s" ["%s" => "%s"]>' % (
            self.title,
            self.from_status_title,
            self.to_status_title)


class RoleMapping(object):
    implements(IRoleMapping)

    def __init__(self, customer_role, plone_role):
        self.customer_role = customer_role
        self.plone_role = plone_role

    def __repr__(self):
        return u'<RoleMapping "%s" => "%s">' % (
            self.customer_role,
            self.plone_role)
