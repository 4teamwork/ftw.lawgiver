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

        input: 'An editor-in-chief can access the worklist.'
        output: "editor-in-chief"
        """
        raise NotImplementedError()

    def convert_role_inheritance_statement(self, statement):
        """Converts a role inheritance statement, returning a tuple with the
        two roles of the statement, e.g.:

        input: 'An administrator can always perform the same actions as an editor.'
        output: ('administrator', 'editor')
        """
        raise NotImplementedError()


    def convert_permission_statement(self, statement):
        """Converts a permission statement, extracting the role and action group
        name from the statement, e.g.:

        input: 'An editor can view this content.'
        output: ('editor', 'view')
        """
        raise NotImplementedError()
