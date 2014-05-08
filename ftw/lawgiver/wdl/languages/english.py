from ftw.lawgiver.wdl import keywords
from ftw.lawgiver.wdl.languages.base import LanguageBase
import re


class English(LanguageBase):

    filename = 'specification.txt'
    code = 'en'

    constraints = {
        keywords.DESCRIPTION: r'^[Dd]escription$',
        keywords.GENERAL: r'^[Gg]eneral$',
        keywords.INITIAL_STATUS: r'^[Ii]nitial [Ss]tatus$',
        keywords.ROLE_MAPPING: r'^[Rr]ole [Mm]apping$',
        keywords.STATUS: r'^[Ss]tatus (.*)$',
        keywords.TRANSITIONS: r'^[Tt]ransitions$',
        keywords.TRANSITION_URL: r'^[Tt]ransition[- ](URL|url)$',
        keywords.VISIBLE_ROLES: r'^[Vv]isible [Rr]oles$',
        keywords.ROLE_DESCRIPTION: r'^(.*?) [Rr]ole [Dd]escription$'
        }

    def cleanup_statement(self, statement):
        """Removes prefix and literals which are not intersting in general.
        """
        # remove leading prefixes
        statement = re.sub(r'^(?:[Aa] |[Aa]n )', '', statement)

        # always
        statement = statement.replace(' can always ', ' can ')

        return statement

    def convert_worklist_statement(self, statement):
        text = self.cleanup_statement(statement.lower())
        match = re.match(r'(.*?) can access the worklist.?', text)
        if match:
            return match.groups()[0]

        else:
            return None

    def convert_role_inheritance_statement(self, statement):
        text = self.cleanup_statement(statement.lower())
        if 'can perform' not in text:
            return None

        text = re.sub(
            r'(?:\.$'
            r'| perform the same(?: actions)? as(?: a[n]?)?'
            r')',
            '', text)

        text = re.sub(' +', ' ', text)
        return tuple(text.split(' can '))

    def convert_permission_statement(self, statement):
        text = self.cleanup_statement(statement)

        # remove trailing "this content" and such.
        text = re.sub(
            r'(?:\.'
            r'| on this conte[nx]t\.?'
            r'| this conte[nx]t\.?'
            r'| the conte[nx]t\.?'
            r'| that conte[nx]t\.?'
            r'| any conte[nx]t\.?'
            r'| new content\.?'
            r'| content\.?'
            r')$',
            '', text)

        # always
        text = text.replace(' can always ', ' can ')

        try:
            role, action = text.split(' can ')
        except ValueError:
            return None

        role = role.lower()
        return role, action
