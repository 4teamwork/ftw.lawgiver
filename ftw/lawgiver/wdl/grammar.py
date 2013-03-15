from ftw.lawgiver.wdl.ast import RoleMapping
from ftw.lawgiver.wdl.ast import Specification
from ftw.lawgiver.wdl.ast import Status
from ftw.lawgiver.wdl.ast import Transition
from ftw.lawgiver.wdl.utils import remember_line_number
from pyparsing import Group
from pyparsing import OneOrMore
from pyparsing import Optional
from pyparsing import Suppress
from pyparsing import Word
from pyparsing import alphanums
from pyparsing import alphas8bit


# Newlines are important for us, remove the from default whitespace chars so
# that we can match them
Group.setDefaultWhitespaceChars('\t ')

# helpers
newline = Suppress("\n")
some_newlines = Suppress(OneOrMore(newline))
words = OneOrMore(Word(alphanums + alphas8bit)).setParseAction(' '.join)

punctuation = '.,[](){}<>:,\'"-_!;?!'
sentence = OneOrMore(Word(alphanums + punctuation + alphas8bit)
                     ).setParseAction(' '.join)


# SPECIFICATION PROPERTIES
TITLE = (
    Suppress(Word('Title:')) +
    sentence +
    newline
    ).setParseAction(''.join).setResultsName('title')

DESCRIPTION = Optional((
        Suppress(Word('Description:')) +
        sentence +
        newline
        ).setParseAction(''.join).setResultsName('description'))

PROPERTIES = TITLE + DESCRIPTION + Optional(some_newlines)


# "States:"
def state_line_to_ast(document, position, tokens):
    if len(tokens) == 2:
        assert tokens[0] == '*'
        obj = Status(title=tokens[1], init=True)
    else:
        obj = Status(title=tokens[0])

    remember_line_number(obj, document, position)
    return obj

state_line = (
    Suppress('-') +
    Optional('*') +
    words +
    Optional(newline)).setParseAction(state_line_to_ast)

STATES = Optional(Group(
        Suppress(Word('States:')) +
        newline +
        OneOrMore(state_line) +
        Optional(some_newlines)).setResultsName('states'))


# "Transitions:"
def transition_line_to_ast(document, position, tokens):
    obj = Transition(*tokens)
    remember_line_number(obj, document, position)
    return obj

transition_line = (
    Suppress('-') +
    words +
    Suppress('(') +
    words +
    Suppress('=>') +
    words +
    Suppress(')') +
    Optional(newline)
    ).setParseAction(transition_line_to_ast)

TRANSITIONS = Optional(Group(
        Suppress(Word("Transitions:")) +
        newline +
        OneOrMore(transition_line) +
        Optional(some_newlines)).setResultsName('transitions'))


# "Role mapping:"
def role_mapping_line_to_ast(document, position, tokens):
    obj = RoleMapping(*tokens)
    remember_line_number(obj, document, position)
    return obj

role_mapping_line = (
    Suppress('-') +
    sentence +
    Suppress('=>') +
    sentence +
    Optional(newline)
    ).setParseAction(role_mapping_line_to_ast)

ROLE_MAPPINGS = Optional(Group(
        Suppress(Word("Role mapping:")) +
        newline +
        OneOrMore(role_mapping_line) +
        Optional(some_newlines)).setResultsName('role_mappings'))


# Specification

def spec_to_ast(document, position, tokens):
    return Specification(**dict(tokens))


WORKFLOW_SPEC = (
    PROPERTIES + (STATES & TRANSITIONS & ROLE_MAPPINGS)
    ).setParseAction(spec_to_ast)
