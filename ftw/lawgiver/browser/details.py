from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.GenericSetup.utils import importObjects
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from ftw.lawgiver import _
from ftw.lawgiver.interfaces import IPermissionCollector
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.publisher.browser import BrowserView
from zope.publisher.interfaces import IPublishTraverse
import os.path
import sys


@implementer(IPublishTraverse)
class SpecDetails(BrowserView):

    confirmation = ViewPageTemplateFile('templates/import-confirmation.pt')

    def __init__(self, context, request):
        super(SpecDetails, self).__init__(context, request)
        self._spec_hash = None
        self.specification = None

    def publishTraverse(self, request, name):
        # stop traversing, we have arrived
        request['TraversalRequestNameStack'] = []

        self._spec_hash = name
        return self

    def __call__(self, *args, **kwargs):
        self.specification = self._load_specification()

        if 'confirmation.cancelled' in self.request.form:
            return self.reload()

        if 'update_security' in self.request.form:
            self.update_security()
            return self.reload()

        if not self.specification:
            return self.index()

        if 'write_workflow' in self.request.form:
            self.write_workflow()
            return self.reload()

        if 'write_and_import' in self.request.form:
            return self.write_and_import_workflow()

        return self.index()

    def reload(self):
        """Redirects to itself for purging request data, so
        that a Ctrl-R reloads the page and does not execute things
        such as writing the workflow.
        """
        return self.request.RESPONSE.redirect(self.request.URL)

    def is_confirmed(self):
        return 'confirmation.confirmed' in self.request.form

    def render_confirmation(self):
        return self.confirmation()

    def is_destructive(self):
        return len(self.removing_states()) > 0

    def removing_states(self):
        """Returns the states that will be removed upon writing and importing
        the current spec.
        """
        wftool = getToolByName(self.context, 'portal_workflow')
        wf = wftool.get(self.workflow_name())

        if not wf:
            return []

        current_states = wf.states.keys()

        generator = getUtility(IWorkflowGenerator)
        new_states = generator.get_states(
            self.workflow_name(), self.specification)

        return list(set(current_states) - set(new_states))

    def write_workflow(self):
        generator = getUtility(IWorkflowGenerator)
        try:
            generator(self.workflow_name(), self.specification)

        except ConflictError:
            raise

        except Exception, exc:
            getSite().error_log.raising(sys.exc_info())

            IStatusMessage(self.request).add(
                _(u'error_while_generating_workflow',
                  default=u'Error while generating the workflow: ${msg}',
                  mapping={'msg': str(exc)}),
                type='error')

            return False

        else:
            with open(self.get_definition_path(), 'w+') as result_file:
                generator.write(result_file)

            IStatusMessage(self.request).add(
                _(u'info_workflow_generated',
                  default=u'The workflow was generated to ${path}.',
                  mapping={'path': self.get_definition_path()}))

            return True

    def write_and_import_workflow(self):
        if self.is_destructive() and not self.is_confirmed():
            return self.render_confirmation()

        if not self.write_workflow():
            return self.reload()

        setup_tool = getToolByName(self.context, 'portal_setup')
        profile_id = self._find_profile_name_for_workflow()
        import_context = setup_tool._getImportContext(
            profile_id, None, None)

        workflow = self._get_or_create_workflow_obj()
        parent_path = 'workflows/'
        importObjects(workflow, parent_path, import_context)

        IStatusMessage(self.request).add(
            _(u'info_workflow_imported',
              default=u'Workflow ${wfname} successfully imported.',
              mapping={'wfname': self.workflow_name()}))

        return self.reload()

    def update_security(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        updated_objects = wftool.updateRoleMappings()

        IStatusMessage(self.request).add(
            _(u'info_security_updated',
              default=u'Security update: ${amount} objects updated.',
              mapping={'amount': updated_objects}))

    def _get_or_create_workflow_obj(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        name = self.workflow_name()

        if name not in wftool.objectIds():
            import Products
            factory = next(info['instance'] for info in Products.meta_types
                           if info['name'] == 'Workflow')
            assert factory, 'Could not find meta_type factory for "Workflow".'

            wftool._setObject(name, factory(name))

        return wftool[name]

    def _find_profile_name_for_workflow(self):
        setup_tool = getToolByName(self.context, 'portal_setup')
        profile_path = os.path.abspath(os.path.join(
                os.path.dirname(self.get_definition_path()),
                '..', '..'))

        for profile in setup_tool.listProfileInfo():
            if profile.get('path') == profile_path:
                return 'profile-%s' % profile.get('id')

        raise AttributeError('Profile for workflow %s not found' % (
                self.get_definition_path()))

    def _load_specification(self):
        parser = getUtility(IWorkflowSpecificationParser)
        path = self.get_spec_path()

        with open(path) as specfile:
            try:
                return parser(specfile)
            except Exception, exc:
                getSite().error_log.raising(sys.exc_info())

                IStatusMessage(self.request).add(
                    _(u'error_parsing_error',
                      default=u'The specification file could not be'
                      u' parsed: ${error}',
                      mapping={'error': str(exc).decode('utf-8')}),
                    type='error')
                return None

    def is_workflow_installed(self):
        wftool = getToolByName(self.context, 'portal_workflow')
        return wftool.getWorkflowById(self.workflow_name()) and True or False

    def workflow_name(self):
        path = self.get_spec_path()
        return os.path.basename(os.path.dirname(path))

    def raw_specification(self):
        path = self.get_spec_path()
        with open(path) as specfile:
            # handle errors
            return specfile.read()

    def get_spec_path(self):
        discovery = getMultiAdapter((self.context, self.request),
                                    IWorkflowSpecificationDiscovery)

        assert self._spec_hash, \
            'Spec hash was not set in traversal: "%s"' % str(self._spec_hash)

        path = discovery.unhash(self._spec_hash)
        if path is None:
            raise ValueError(
                'Could not find any specification with hash "%s"' % str(
                    self._spec_hash))

        return path

    def get_definition_path(self):
        """Path to workflow definition file.
        """
        return os.path.join(os.path.dirname(self.get_spec_path()),
                            'definition.xml')

    def get_permissions(self):
        workflow_name = self.workflow_name()
        collector = getUtility(IPermissionCollector)
        managed = collector.get_grouped_permissions(
            workflow_name, unmanaged=True)
        unmanaged = managed['unmanaged']
        del managed['unmanaged']

        return {'managed': managed,
                'unmanaged': unmanaged}

    def pot_data(self):
        return self._get_translations(fill_default=False)

    def po_data(self):
        return self._get_translations(fill_default=True)

    def _get_translations(self, fill_default):
        if self.specification is None:
            return ''

        generator = getUtility(IWorkflowGenerator)

        translations = generator.get_translations(self.workflow_name(),
                                                  self.specification)

        lines = []
        for msgid in sorted(translations.keys()):
            if fill_default:
                default = translations[msgid]
            else:
                default = ''

            lines.extend((
                    'msgid "%s"' % msgid.decode('utf-8'),
                    'msgstr "%s"' % default.decode('utf-8'),
                    ''))

        return '\n'.join(lines).strip()
