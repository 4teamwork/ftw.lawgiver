# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument


from zope.interface import Attribute
from zope.interface import Interface


class IWorkflowSpecificationParser(Interface):
    """The workflow specification parser utility parsers a input stream
    to a abstract syntax tree.
    """

    def __call__(stream, path=None, silent=False):
        """Parse the stream and return the validated abstract syntax tree.
        If `silent` is `True` it returns `None` on any error.
        """


class ISpecification(Interface):
    """Represents a specification file.
    """

    title = Attribute(u'The workflow title.')
    description = Attribute('The workflow description.')
    states = Attribute('A list of `IStatus` objects.')
    transitions = Attribute('A list of `ITransition` objects.')
    role_mappings = Attribute('A list of `IRoleMapping` objects.')

    def get_initial_status():
        """Returns the `IStatus` object of the initial status.
        """

    def validate():
        """Validates the specification.
        Raises an exception when an error occurs,
        otherwise the validation is considered as passed.
        """


class IStatus(Interface):
    """A workflow status representation.
    """

    def __init__(title, statements):
        """Construct a status object with a `title` and a list of
        `statements`.
        """

    title = Attribute(u'The workflow status title.')
    statements = Attribute(u'List of statements of this workflow.')


class ITransition(Interface):
    """Represents a workflow transition.
    """

    def __init__(title, src_status, dest_status):
        """Expects a string `title` and from / to status (title of the
        status).
        """

    title = Attribute(u'The workflow transition title.')
    src_status = Attribute(u'The source status of the transition.')
    dest_status = Attribute(u'The target status of the transition.')
