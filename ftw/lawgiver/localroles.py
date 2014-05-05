from OFS.interfaces import IApplication
from Products.CMFPlone import PloneMessageFactory
from ftw.lawgiver.interfaces import IDynamicRoleAdapter
from ftw.lawgiver.utils import get_workflow_for
from plone.app.workflow import permissions
from plone.app.workflow.interfaces import ISharingPageRole
from zope.component import adapter
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import Interface
from zope.interface import implementer
from zope.interface import implements


DEFAULT_ROLE_TITLES = {
    'Reader': PloneMessageFactory(u"title_can_view", default=u"Can view"),
    'Editor': PloneMessageFactory(u"title_can_edit", default=u"Can edit"),
    'Contributor': PloneMessageFactory(u"title_can_add", default=u"Can add"),
    'Reviewer': PloneMessageFactory(u"title_can_review",
                                    default=u"Can review"),
    }


class DynamicRolesUtility(object):
    implements(ISharingPageRole)

    def __init__(self, plonerole):
        self.plonerole = plonerole

    @property
    def title(self):
        return self.get_role_adapter().get_title()

    @property
    def required_permission(self):
        return self.get_role_adapter().get_required_permission()

    def get_role_adapter(self):
        site = getSite()
        request = site.REQUEST
        context = request.PARENTS[0]
        if IApplication.providedBy(context):
            context = site
        return getMultiAdapter((context, request),
                               IDynamicRoleAdapter,
                               name=self.plonerole)


class DynamicRolesAdapter(object):
    implements(IDynamicRoleAdapter)

    def __init__(self, context, request, plonerole, required_permission):
        self.context = context
        self.request = request
        self.plonerole = plonerole
        self.required_permission = required_permission

    def get_title(self):
        default_title = DEFAULT_ROLE_TITLES.get(
            self.plonerole, PloneMessageFactory(self.plonerole))

        workflow = get_workflow_for(self.context)
        if workflow:
            return PloneMessageFactory(
                '%s--ROLE--%s' % (workflow.getId(), self.plonerole),
                default=translate(default_title, context=self.request))

        else:
            return default_title

    def get_required_permission(self):
        return self.required_permission


def create_dynamic_role(plonerole, required_permission):
    @implementer(ISharingPageRole)
    def dynamic_role_utility_factory():
        return DynamicRolesUtility(plonerole)

    @adapter(Interface, Interface)
    @implementer(IDynamicRoleAdapter)
    def dynamic_role_adapter_factory(context, request):
        return DynamicRolesAdapter(context,
                                   request,
                                   plonerole,
                                   required_permission)

    return dynamic_role_utility_factory, dynamic_role_adapter_factory


reader_role_utility, reader_role_adapter = create_dynamic_role(
    'Reader', permissions.DelegateReaderRole)

editor_role_utility, editor_role_adapter = create_dynamic_role(
    'Editor', permissions.DelegateEditorRole)

contributor_role_utility, contributor_role_adapter = create_dynamic_role(
    'Contributor', permissions.DelegateContributorRole)

reviewer_role_utility, reviewer_role_adapter = create_dynamic_role(
    'Reviewer', permissions.DelegateReviewerRole)
