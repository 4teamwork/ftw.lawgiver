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


class ISyntaxTreeElement(Interface):
    """Elements in the abstract syntax tree are implementing this interface
    and provide support for validation and augmenting after parsing and
    creating the tree.
    """

    def recursive_collect_objects(collection):
        """After parsing the document and creating the syntax tree the
        parser calls this method for collecting all objects in the tree
        recursively so that they can be validated afterwards.

        An object implementing this method should add the object itself
        to the `collection` (set) and then call this method on every
        object it knows.

        Most implementations will not have pointers to other objects in
        this state.
        """

    def validate(specification, warnings):
        """The parser calls the validate method on every object found
        with `recursive_collect_objects`.

        The validate can raise a
        `zope.schema.interfaces.ConstraintNotSatisfied` exception when
        there is a fatal error or it can append a warning to the
        passed `warnings` list.

        When neither is done everything is valid.
        """

    def augment(specification):
        """Any object in the AST may need to have pointers to other objects
        but it should not access them on parsing time (they may not
        yet exist).

        The pointers should be created after parsing and validating in this
        `augment` hook by getting them from the `specification`, which is the
        AST root.
        """


class ISpecification(ISyntaxTreeElement):
    """Represents a specification file.
    """

    title = Attribute(u'The workflow title.')
    description = Attribute('The workflow description.')
    states = Attribute('A list of `IStatus` objects.')
    transitions = Attribute('A list of `ITransition` objects.')
    role_mappings = Attribute('A list of `IRoleMapping` objects.')

    def get_status_by_title(title):
        """Returns the status with the title `title` or None.
        """


class IStatus(ISyntaxTreeElement):
    """A workflow status representation.
    """

    def __init__(title, init=False):
        """Construct a status object with a `title`.
        If `init` is `True`, this status is the init status of the workflow.
        """

    title = Attribute(u'The workflow status title.')
    is_init_status = Attribute(
        u'True when this is the init status of this workflow')


class ITransition(ISyntaxTreeElement):
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


class IRoleMapping(ISyntaxTreeElement):
    """Represents a role mapping.
    """

    def __init__(customer_role, plone_role):
        pass

    customer_role = Attribute(u'The customer role (string).')
    plone_role = Attribute(u'The plone role (string).')
