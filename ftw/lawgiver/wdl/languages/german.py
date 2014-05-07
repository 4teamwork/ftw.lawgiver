from ftw.lawgiver.wdl import keywords
from ftw.lawgiver.wdl.languages.base import LanguageBase
import re


class German(LanguageBase):

    filename = 'specification.de.txt'
    code = 'de'

    constraints = {
        keywords.DESCRIPTION: r'^[Bb]eschreibung$',
        keywords.GENERAL: r'^[Aa]llgemein$',
        keywords.INITIAL_STATUS: r'^[Ii]nitial ?[Zz]ustand$',
        keywords.ROLE_MAPPING: r'^[Rr]ollen [Zz]uweisung$',
        keywords.STATUS: r'^[Ss]tatus (.*)$',
        keywords.TRANSITIONS: (r'^(?:'
                               r'[Tt]ransitionen'
                               r'|[Zz]ustands\xc3\xa4nderungen'
                               ')$'),
        keywords.TRANSITION_URL: (r'^(?:URL|url) '
                                  r'(?:'
                                  r'[Tt]ransition(en)*'
                                  r'|[Zz]ustands\xc3\xa4nderung(en)*'
                                  r')$'),
        keywords.VISIBLE_ROLES: r'^[Ss]ichtbare [Rr]ollen$',
        keywords.ROLE_DESCRIPTION: r'^(.*?) [R]ollen ?-?[bB]eschreibung$'
        }

    def cleanup_statement(self, statement):
        """Removes prefix and literals which are not intersting in general.
        """
        # remove leading prefixes
        statement = re.sub(r'^([Ee]in|[Ee]ine|[Dd]er|[Dd]ie) ', '', statement)

        # remove "immer"
        statement = re.sub(r' (?:kann|darf)(.*?) immer ',
                           ' kann\g<1> ',
                           statement)

        # remove trailing dot
        statement = re.sub(r'\.$', '', statement)

        return statement

    def convert_worklist_statement(self, statement):
        text = self.cleanup_statement(statement.lower())
        match = re.match(r'(.*?) hat zugriff auf die arbeitsliste', text)
        if match:
            return match.groups()[0]

        else:
            return None

    def convert_role_inheritance_statement(self, statement):
        text = self.cleanup_statement(statement.lower())
        if 'gleichen rechte' not in text \
                and 'das gleiche' not in text:
            return None

        text = re.sub(
            r' (?:'
            r'hat die gleichen rechte wie'
            r'|kann das gleiche wie'
            r')(?: ein| eine| der| die){0,1}',
            '==>', text)

        return tuple(map(str.strip, text.split('==>')))

    def convert_permission_statement(self, statement):
        text = self.cleanup_statement(statement)

        # remove trailing "this content" and such.
        text = re.sub(
            r'(?:\.'
            r'| den [Ii]nhalt'
            r'| diesen [Ii]nhalt'
            r'| auf diesem [Ii]nhalt'
            r'| jeden [Ii]nhalt'
            r'| alle [Ii]nhalte'
            r'| neuen? [Ii]nhalte?'
            r'| [Ii]nhalte(?! konfigurieren)'
            r')',
            '', text)

        try:
            role, _, action = re.split(' (kann|darf) ', text)
        except ValueError:
            return None

        role = role.lower()
        return role, action
