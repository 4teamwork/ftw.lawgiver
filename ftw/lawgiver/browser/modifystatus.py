from AccessControl import getSecurityManager
from contextlib import contextmanager
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest
from zope.publisher.browser import BrowserView

try:
    from plone.protect.utils import addTokenToUrl
except ImportError:
    # Plone 4 ships plone.protect 2.x, missing `addTokenToUrl`.
    HAS_MODERN_PLONE_PROTECT = False
else:
    # Plone >= 5 ships plone.protect 3.x featuring `addTokenToUrl`.
    HAS_MODERN_PLONE_PROTECT = True


class ModifyStatusViewBase(BrowserView):
    """The ModifyStatusViewBase is a base class for implementing custom behavior when executing
    workflow transitions.
    See the readme for usage instructions.
    """

    def __call__(self):
        transition = self.request.get('transition')
        if not transition:
            raise BadRequest('transition')

        handler = self._interceptors.get(
            transition, self.__class__.redirect_to_content_status_modify)
        return handler(self, self.context, transition)

    def execute_transition(self, context, transition, **kwargs):
        kwargs['workflow_action'] = transition
        return context.restrictedTraverse('content_status_modify')(**kwargs)

    def redirect_to_content_status_modify(self, context, transition):
        target_url = '{}/content_status_modify?workflow_action={}'.format(
            context.absolute_url(), transition)

        if HAS_MODERN_PLONE_PROTECT:
            target_url = addTokenToUrl(target_url)

        return self.request.response.redirect(target_url)

    def set_workflow_state(self, context, review_state, **infos):
        """Set the workflow status of the context to the given review state.
        """
        infos['review_state'] = review_state
        infos.setdefault('action', '')
        infos.setdefault('actor', getSecurityManager().getUser().getId())
        infos.setdefault('time', DateTime())
        infos.setdefault('comments', '')

        portal_workflow = getToolByName(self.context, 'portal_workflow')
        workflow_name = portal_workflow.getChainFor(context)[0]
        portal_workflow.setStatusOf(workflow_name, context, infos)
        for workflow in portal_workflow.getWorkflowsFor(context):
            workflow.updateRoleMappingsFor(context)

        context.reindexObjectSecurity()
        context.reindexObject(idxs=['review_state'])

    @contextmanager
    def in_state(self, context, review_state):
        """Temporarily put the object in a certain review state in order to apply
        changes with the security settings of the temporary state.
        """
        portal_workflow = getToolByName(self.context, 'portal_workflow')
        ori_history = context.workflow_history
        context.workflow_history = context.workflow_history.copy()
        self.set_workflow_state(context, review_state)
        try:
            yield
        finally:
            context.workflow_history = ori_history
            for workflow in portal_workflow.getWorkflowsFor(context):
                workflow.updateRoleMappingsFor(context)

    def redirect_to(self, context):
        return self.request.response.redirect(context.absolute_url())

    @classmethod
    def intercept(cls, *transitions):
        argname = '_interceptors'
        if argname not in dir(cls):
            setattr(cls, argname, {})

        registry = getattr(cls, argname)
        def decorator(func):
            for transition_name in transitions:
                registry[transition_name] = func
            return func
        return decorator
