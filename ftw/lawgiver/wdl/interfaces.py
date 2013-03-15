# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument


from zope.interface import Attribute
from zope.interface import Interface


class IWorkflowSpecificationParser(Interface):
    """The workflow specification parser utility parsers a input stream
    to a abstract syntax tree.
    """

    def parse(stream):
        """Parse the stream and return the validated abstract syntax tree.
        """


class ISpecification(Interface):
    """Represents a specification file.
    """

    title = Attribute(u'The workflow title.')
    description = Attribute('The workflow description.')
    states = Attribute('A list of `IStatus` objects.')
    transitions = Attribute('A list of `ITransition` objects.')
    role_mappings = Attribute('A list of `IRoleMapping` objects.')


class IStatus(Interface):
    """A workflow status representation.
    """

    def __init__(title, init=False):
        """Construct a status object with a `title`.
        If `init` is `True`, this status is the init status of the workflow.
        """

    title = Attribute(u'The workflow status title.')
    is_init_status = Attribute(
        u'True when this is the init status of this workflow')


class ITransition(Interface):
    """Represents a workflow transition.
    """

    def __init__(title, from_status, to_status):
        """Expects a string `title` and from / to status (title of the
        status).
        """

    title = Attribute(u'The workflow transition title.')

    def get_from_status():
        """Returns an `IStatus` object of the source status of this
        transition.
        """

    def get_to_status():
        """Returns an `IStatus` object of the destination status of this
        transition.
        """


class IRoleMapping(Interface):
    """Represents a role mapping.
    """

    def __init__(customer_role, plone_role):
        pass

    customer_role = Attribute(u'The customer role (string).')
    plone_role = Attribute(u'The plone role (string).')
