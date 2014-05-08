from Acquisition import aq_inner
from Acquisition import aq_parent
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
import os.path


def get_workflow_for(context):
    wftool = getToolByName(getSite(), 'portal_workflow')

    while context and not IContentish.providedBy(context):
        context = aq_parent(aq_inner(context))
    if not context:
        return None

    workflows = wftool.getWorkflowsFor(context)
    if len(workflows) == 0:
        return None
    else:
        return workflows[0]


def get_specification(workflow_id):
    discovery = getMultiAdapter((getSite(), getSite().REQUEST),
                        IWorkflowSpecificationDiscovery)
    parser = getUtility(IWorkflowSpecificationParser)

    for path in discovery.discover():
        if os.path.basename(os.path.dirname(path)) != workflow_id:
            continue

        with open(path) as specfile:
            return parser(specfile, path=path, silent=True)

    return None


def get_specification_for(context):
    workflow = get_workflow_for(context)
    if not workflow:
        return None

    return get_specification(workflow.id)


def merge_role_inheritance(specification, status):
    """
    - merges status role inheritance and global (general)
    role inheritance

    - translates customer roles into plone roles
    """

    customer_roles = set(specification.role_inheritance)
    customer_roles.update(set(status.role_inheritance))

    result = []
    for inheritor_role, base_role in customer_roles:
        result.append((
                specification.role_mapping[inheritor_role],
                specification.role_mapping[base_role]))

    return result


def get_roles_inheriting_from(roles, role_inheritance):
    """Accepts a list of original roles and a role inheritance
    list (from `merge_role_inheritance`).
    Returned is the recursively resolved list of roles which
    are inheriting the original roles.

    e.g.:
    A inherits from B
    B inherits from C
    role_inheritance = (('A', 'B'), ('B', 'C'))

    get_roles_inheriting_from(['A'], role_inheritance) -> ['A']
    get_roles_inheriting_from(['B'], role_inheritance) -> ['A', 'B']
    get_roles_inheriting_from(['C'], role_inheritance) -> ['A', 'B', 'C']
    """

    if not role_inheritance:
        return roles

    roles = roles[:]

    # role_inheritance is: [('inheritor', 'base'), ('inheritor2', 'base')]
    # make: {'base': ['inheritor', 'inheritor2']}
    base_roles = set(zip(*role_inheritance)[1])
    mapping = dict([(key, []) for key in base_roles])
    for inheritor, base in role_inheritance:
        mapping[base].append(inheritor)

    def _recurse(role, mapping, result):
        if role not in mapping:
            return

        for alias in mapping[role]:
            if alias not in result:
                result.append(alias)
                _recurse(alias, mapping, result)

    for role in roles[:]:
        _recurse(role, mapping, roles)

    return sorted(roles)


def get_roles_inherited_by(roles, role_inheritance):
    """Accepts a list of original roles and a role inheritance
    list (from `merge_role_inheritance`).

    Return is the list of roles which the original roles inherit,
    recursively.

    e.g.
    A inherits from B
    B inherits from C
    role_inheritance = (('A', 'B'), ('B', 'C'))

    get_roles_inherited_by(['A'], role_inheritance) -> ['A', 'B', 'C']
    get_roles_inherited_by(['B'], role_inheritance) -> ['B', 'C']
    get_roles_inherited_by(['C'], role_inheritance) -> ['C']
    """

    result = []

    def _recurse(role):
        if role in result:
            return
        result.append(role)
        map(_recurse, [parent for (child, parent) in role_inheritance
                       if child == role])

    map(_recurse, roles)
    return result
