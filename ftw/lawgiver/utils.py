from Acquisition import aq_inner
from Acquisition import aq_parent
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.lawgiver.wdl.parser import LowerCaseString
from path import Path
from plone.app.workflow.interfaces import ISharingPageRole
from Products.CMFCore.interfaces import IContentish
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite
from zope.i18nmessageid import Message
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


def generate_role_translation_id(workflow_id, role):
    """Generate and return the translation ID which used for translating
    a role for a specific workflow (in the ``plone`` translation domain).
    """
    if isinstance(role, LowerCaseString):
        role = role.original

    return '{0}--ROLE--{1}'.format(workflow_id, role)


def translate_role_for_workflow(workflow_id, role):
    """Returns a message object which translates the role for this
    workflow, with fallback to Plone's default translation.
    """
    from ftw.lawgiver.localroles import DEFAULT_ROLE_TITLES

    if isinstance(role, LowerCaseString):
        role = role.original

    fallback = role

    if role in DEFAULT_ROLE_TITLES:
        fallback = DEFAULT_ROLE_TITLES[role]

    else:
        utility = queryUtility(ISharingPageRole, name=role)
        if utility:
            fallback = utility.title

    return Message(generate_role_translation_id(workflow_id, role),
                   domain='plone',
                   default=fallback)


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


def in_development(path):
    """Returns True when the path is in development (source checkout).
    """
    return not ('egg' in path or 'site-packages' in path)


def find_egginfo(path):
    path = Path(path)
    if not path or path == '/':
        raise ValueError('WARNING: no *.egg-info directory could be found.')
        return None

    egginfos = path.dirs('*.egg-info')
    if len(egginfos) == 0:
        return find_egginfo(path.dirname())

    if len(egginfos) > 1:
        raise ValueError('WARNING: more than one *.egg-info  directory found.')
        return None

    return egginfos[0]
