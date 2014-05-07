from ftw.lawgiver.exceptions import ParsingError
from ftw.lawgiver.wdl import keywords
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.lawgiver.wdl.languages import LANGUAGES
from ftw.lawgiver.wdl.specification import Specification
from ftw.lawgiver.wdl.specification import Status
from ftw.lawgiver.wdl.specification import Transition
from ordereddict import OrderedDict
from zope.interface import implements
import ConfigParser
import os.path
import re


class LowerCaseString(str):

    def __new__(klass, text):
        self = str.__new__(klass, text.lower())
        self.original = text
        return self


def consumer(keyword):
    """Decorator for consuming a certain kind of option.
    The decorator is initialized with a keyword constant, from which the
    language specific regular expression for matching the consumer can
    be found.

    The method gets a ``specargs`` dict passed in which will be used as
    keyword arguments for creating the Specification object.

    Example usage:

    >>> @consumer(keywords.DESCRIPTION)
    ... def convert_description(self, match, value, specargs):
    ...     specargs['description'] = value
    """

    def _decorator(func):
        func.consumer_keyword = keyword
        return func
    return _decorator


PERMISSION_STATEMENT = 'permission statement'
ROLE_INHERITANCE_STATEMENT = 'role inheritance statement'
WORKLIST_STATEMENT = 'worklist statement'


def convert_statement(language, statement):
    result = language.convert_worklist_statement(statement)
    if result:
        return WORKLIST_STATEMENT, result

    result = language.convert_role_inheritance_statement(statement)
    if result:
        return ROLE_INHERITANCE_STATEMENT, result

    result = language.convert_permission_statement(statement)
    if result:
        return PERMISSION_STATEMENT, result

    raise ParsingError('Unkown statement format: "%s"' % statement)


class SpecificationParser(object):

    implements(IWorkflowSpecificationParser)

    def __init__(self):
        self._config = None
        self._spec = None

    def __call__(self, stream, path=None, silent=False):
        try:
            return self._parse(stream, path=path)
        except (ParsingError, ConfigParser.ParsingError):
            if silent:
                return None
            else:
                raise

    def _parse(self, stream, path=None):
        locals()['__traceback_info__'] = (stream, path)
        self._read_stream(stream)
        self.language = self._guess_language(path)
        self._convert()
        self._post_converting()
        return self._spec

    def _read_stream(self, stream):
        """Parse `stream` into a configparser `self._config` object.
        """

        self._config = ConfigParser.RawConfigParser()
        self._config.optionxform = str  # do not lowercase tokens
        self._config.readfp(stream)

    def _convert(self):
        """Convert the configparser `self._config` into a ISpecification
        object (`self._spec`).
        """

        if len(self._config.sections()) != 1:
            raise ParsingError(
                'Exactly one ini-style section is required,'
                ' containing the workflow title.')

        sectionname = self._config.sections()[0]
        specargs = {'title': sectionname,
                    'states': OrderedDict(),
                    'language': self.language}

        for name, value in self._config.items(sectionname):
            self._call_consumer(name, value, specargs)

        self._spec = Specification(**specargs)

    def _guess_language(self, path):
        if path is None:
            return LANGUAGES['en']

        filename = os.path.basename(path)
        for language in LANGUAGES.values():
            if filename == language.filename:
                return language

        return LANGUAGES['en']

    @consumer(keywords.DESCRIPTION)
    def _convert_description(self, match, value, specargs):
        specargs['description'] = value

    @consumer(keywords.INITIAL_STATUS)
    def _convert_initial_status(self, match, value, specargs):
        specargs['initial_status_title'] = value

    @consumer(keywords.TRANSITION_URL)
    def _convert_transition_url(self, match, value, specargs):
        specargs['custom_transition_url'] = value

    @consumer(keywords.STATUS)
    def _convert_status(self, match, value, specargs):
        title = match.groups()[0]

        statements = []
        role_inheritance = []
        worklist_viewers = []

        if value.strip():
            lines = map(str.strip, value.strip().split('\n'))
            for line in lines:
                type_, item = convert_statement(self.language, line)
                if type_ == PERMISSION_STATEMENT:
                    statements.append(item)
                elif type_ == ROLE_INHERITANCE_STATEMENT:
                    role_inheritance.append(item)
                elif type_ == WORKLIST_STATEMENT:
                    worklist_viewers.append(item)

        specargs['states'][title] = Status(title, statements,
                                           role_inheritance,
                                           worklist_viewers)

    @consumer(keywords.TRANSITIONS)
    def _convert_transitions(self, match, value, specargs):
        raw = map(str.strip, value.strip().split('\n'))
        transitions = specargs['transitions'] = []

        for line in raw:
            transitions.append(self._convert_transition_line(line))

    def _convert_transition_line(self, line):
        xpr = re.compile(r'([^\(]*?) ?\(([^=]*?) ?=> ?([^\(]*)\)')
        match = xpr.match(line)
        if not match:
            raise ParsingError(
                'Transition line has an invalid format: "%s"' % line)

        title, src_status_title, dest_status_title = match.groups()
        return Transition(title=title,
                          src_status_title=src_status_title,
                          dest_status_title=dest_status_title)

    @consumer(keywords.ROLE_MAPPING)
    def _convert_role_mapping(self, match, value, specargs):
        lines = map(str.strip, value.strip().split('\n'))
        xpr = re.compile(r'^([^=]*?) ?=> ?(.*)$')
        mapping = specargs['role_mapping'] = {}

        for line in lines:
            match = xpr.match(line)
            if not match:
                raise ParsingError('Invalid format in role mapping: "%s"' % (
                        line))

            customer_role, plone_role = match.groups()
            mapping[LowerCaseString(customer_role)] = plone_role

    @consumer(keywords.VISIBLE_ROLES)
    def _convert_visible_roles(self, match, value, specargs):
        lines = map(lambda line: line.strip().lower(),
                    value.strip().split('\n'))
        specargs['visible_roles'] = lines

    @consumer(keywords.ROLE_DESCRIPTION)
    def _convert_role_description(self, match, value, specargs):
        if 'role_descriptions' not in specargs:
            specargs['role_descriptions'] = {}

        role = match.groups()[0]
        text = ' '.join(map(str.strip, value.split('\n'))).strip()
        specargs['role_descriptions'][role] = text

    @consumer(keywords.GENERAL)
    def _convert_general_statements(self, match, value, specargs):
        statements = specargs['generals'] = []
        role_inheritance = specargs['role_inheritance'] = []

        lines = map(str.strip, value.strip().split('\n'))
        for line in lines:
            type_, item = convert_statement(self.language, line)
            if type_ == PERMISSION_STATEMENT:
                statements.append(item)

            elif type_ == ROLE_INHERITANCE_STATEMENT:
                role_inheritance.append(item)

            elif type_ == WORKLIST_STATEMENT:
                raise ParsingError('Worklist statements are not allowed'
                                   ' in the "General" section.')

    def _post_converting(self):
        for transition in self._spec.transitions:
            transition.augment_states(self._spec.states)

    def _call_consumer(self, optname, optvalue, specargs):
        for constraint, func in self._get_consumers():
            match = constraint.match(optname)
            if match:
                return func(match, optvalue, specargs)

        raise ParsingError('The option "%s" is not valid.' % optname)

    def _get_consumers(self):
        consumers = []

        for name in dir(self):
            item = getattr(self, name, None)
            if not callable(item):
                continue

            consumer_keyword = getattr(item, 'consumer_keyword', None)
            if consumer_keyword:
                consumer_constraint = self.language.get_constraint(
                    consumer_keyword)
                consumers.append((consumer_constraint, item))

        return consumers
