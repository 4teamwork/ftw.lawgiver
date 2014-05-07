from ftw.lawgiver.wdl.interfaces import ISpecification
from ftw.lawgiver.wdl.interfaces import IStatus
from ftw.lawgiver.wdl.interfaces import ITransition
from ftw.lawgiver.wdl.languages import LANGUAGES
from zope.interface import implements


class Specification(object):
    implements(ISpecification)

    def __init__(self, title, description=None,
                 states=None, initial_status_title=None,
                 transitions=None, role_mapping=None, generals=None,
                 custom_transition_url=None,
                 role_inheritance=None,
                 visible_roles=None,
                 role_descriptions=None,
                 language=None):
        self.title = title
        self.language = language or LANGUAGES['en']
        self.description = description
        self._initial_status_title = initial_status_title
        self.states = states or {}
        self.transitions = transitions or []
        self.role_mapping = role_mapping or {}
        self.role_descriptions = role_descriptions or {}
        self.generals = generals or []
        self.custom_transition_url = custom_transition_url
        self.role_inheritance = role_inheritance or []
        self.visible_roles = visible_roles

    def __repr__(self):
        return '<Specification "%s">' % self.title

    def get_initial_status(self):
        return self.states.get(self._initial_status_title)

    def validate(self):
        if not self._initial_status_title:
            raise ValueError('No initial status defined.')

        if not self.get_initial_status():
            raise ValueError(
                'Definition of initial status "%s" not found.' % (
                    self._initial_status_title))

        if self.visible_roles:
            for role in self.visible_roles:
                if role not in self.role_mapping:
                    raise ValueError(
                        '"%s" in visible roles is not in role mapping.' % (
                            role))

        if self.role_descriptions:
            for role in self.role_descriptions:
                if role not in self.role_mapping:
                    raise ValueError(
                        '"%s" in role description is not in role mapping.' % (
                            role))


class Status(object):
    implements(IStatus)

    def __init__(self, title, statements, role_inheritance=None,
                 worklist_viewers=None):
        self.title = title
        self.statements = statements
        self.role_inheritance = role_inheritance or []
        self.worklist_viewers = worklist_viewers or []

    def __repr__(self):
        return '<Status "%s">' % self.title


class Transition(object):
    implements(ITransition)

    def __init__(self, title, src_status=None, dest_status=None,
                 src_status_title=None, dest_status_title=None):
        self.title = title

        if src_status is None and src_status_title is None:
            raise ValueError('src_status or src_status_title required.')

        if dest_status is None and dest_status_title is None:
            raise ValueError('dest_status or dest_status_title required.')

        self.src_status = src_status
        self._src_status_title = src_status_title or src_status.title
        self.dest_status = dest_status
        self._dest_status_title = dest_status_title or dest_status.title

    def __repr__(self):
        return '<Transition "%s" ["%s" => "%s"]>' % (
            self.title,
            self.src_status and self.src_status.title,
            self.dest_status and self.dest_status.title)

    def augment_states(self, states):
        if not self.src_status and self._src_status_title not in states:
            raise ValueError('No such src_status "%s" (%s).' % (
                    self._src_status_title, self.title))

        elif not self.src_status:
            self.src_status = states[self._src_status_title]

        if not self.dest_status and self._dest_status_title not in states:
            raise ValueError('No such dest_status "%s" (%s).' % (
                    self._dest_status_title, self.title))

        elif not self.dest_status:
            self.dest_status = states[self._dest_status_title]
