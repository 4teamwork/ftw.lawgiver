import re


class LanguageBase(object):

    filename = None

    constraints = {}

    def get_constraint(self, keyword):
        return re.compile(self.constraints[keyword])

    def cleanup_statement(self, statement):
        """Removes prefix and literals which are not intersting in general.
        """
        return statement

    def convert_worklist_statement(self, statement):
        """Extracts and returns the role from an worklist statement,
        e.g. for english:

        in: 'An editor-in-chief can access the worklist.'
        out: "editor-in-chief"
        """
        raise NotImplementedError()

    def convert_role_inheritance_statement(self, statement):
        """Converts a role inheritance statement, returning a tuple with the
        two roles of the statement, e.g.:

        in: 'An administrator can always perform the same actions as an editor'
        out: ('administrator', 'editor')
        """
        raise NotImplementedError()

    def convert_permission_statement(self, statement):
        """Converts a permission statement, extracting the role and action group
        name from the statement, e.g.:

        in: 'An editor can view this content.'
        out: ('editor', 'view')
        """
        raise NotImplementedError()
