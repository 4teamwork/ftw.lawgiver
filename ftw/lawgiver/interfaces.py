# pylint: disable=E0211, E0213
# E0211: Method has no argument
# E0213: Method should have "self" as first argument


from zope.interface import Interface


class ILawgiverLayer(Interface):
    """ftw.lawgiver package browser layer.
    """


class IActionGroupRegistry(Interface):
    """An action group registry is an utility which knows all the action
    groups and which permissions are mapped to which action group.
    """

    def update(action_group, permissions, workflow=None):
        """Registers new `permissions` (each a string) to a `action_group`,
        optional only for a specific `workflow`.
        """

    def get_action_groups_for_workflow(workflow_name):
        """Returns a action groups to permissions mapping for a specific
        workflow (by `workflow_name`).

        The result is a dict where the key is the action group name and
        the value is a list of permissions (string).
        """

    def get_action_group_for_permission(permission_title, workflow_name=None):
        """Returns the name of the action group a permission is mapped to.
        Optional the `workflow_name` can be passed to make the query workflow
        specific.
        If the permission is not mapped, None is returned.
        """


class IWorkflowGenerator(Interface):
    """The workflow generator utility generates a workflow ``definition.xml``
    from a ``ISpecification`` object.
    """

    def __call__(worfklow_id, specification, result_stream):
        """Converts the ``specification`` into XML and writes the result on
        the ``result_stream``.
        """


class IPermissionCollector(Interface):
    """The permission collector utility decides which permissions will be
    managed by the workflows.

    The default strategy is to ask the action group registry by collecting
    all permissions which have an action group registered either specific
    for this workflow or for `None`, which is the default when no workflow
    specific actions are mapped.
    The list of permissions is reduced to only contain registered
    permissions, meaning those who have an IPermission utility registered.

    For changing the managed permissions for a specific workflow a custom
    IPermissionCollector can be registered as named utilty where the name
    of the utility should match the workflow name (workflow id).
    """

    def collect(workflow_name):
        """Return a list of permission titles to manage.
        """

    def is_permission_registered(permission_title):
        """Returns `True` when the permission with the `permission_title`
        is registered as IPermission utility.

        Registering the utility is usually done either by using the
        default <permission> ZCML or by registering it in an initialize
        function (Archetypes).
        """


class IWorkflowSpecificationDiscovery(Interface):
    """The workflow specification discovery adapter finds workflow
    specifications in generic setup profiles.

    A valid workflow specification file has a path (relative to a generic
    setup profile) with the format:
    `workflows/${workflow ID}/specification.txt`.

    Example:

    - package name: `my.package`

    - generic setup profile path:
    `.../src/my.package/my/package/profiles/default`

    - workflow id: `basic_intranet_workflow`

    - workflow specification:
    `.../profiles/default/workflows/basic_intranet_workflow/specification.txt`

    - workflow definition:
    `.../profiles/default/workflows/basic_intranet_workflow/definition.xml`
    """

    def __init__(context, request):
        """The adapter adapts context and request.
        The request is adapted so that it can be easily customized with
        browser layers.
        """

    def discover():
        """Returns a list absolute paths to specification text files.
        """

    def hash(path):
        """Returns a static hash for a `path`, which can be used as ID for
        the specification.
        The path should not be used as ID in browser communication becuase
        it is unsafe - the hash should be used in this case.
        """

    def unhash(hash):
        """Returns the path to a specification for a hash.
        Only registered paths (which are returned by `discover`) are returned.
        If there is no match `None` is returned.
        """
