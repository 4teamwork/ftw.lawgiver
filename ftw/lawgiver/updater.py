from ftw.lawgiver import _
from ftw.lawgiver.i18nbuilder import I18nBuilder
from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.utils import in_development
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.interface import implements
import os.path
import sys


class Updater(object):
    implements(IUpdater)

    def update_all_specifications(self, statusmessages=False):
        discovery = getMultiAdapter((getSite(), getSite().REQUEST),
                                    IWorkflowSpecificationDiscovery)
        for specification_path in discovery.discover():
            if not in_development(specification_path):
                if statusmessages:
                    IStatusMessage(getSite().REQUEST).add(
                        _(u'warning_skipped_released_spec',
                          default=u'${id}: Skipping released specification.',
                          mapping={
                                'id': self._workflow_id(specification_path)}),
                        type='warning')
                continue

            self.write_workflow(specification_path,
                                statusmessages=statusmessages)
            self.update_translations(specification_path,
                                     statusmessages=statusmessages)

    def write_workflow(self, specification_path, statusmessages=False):
        specification = self._get_specification(specification_path,
                                                statusmessages=statusmessages)
        if not specification:
            return False

        generator = getUtility(IWorkflowGenerator)
        try:
            generator(self._workflow_id(specification_path),
                      specification)
        except ConflictError:
            raise
        except Exception, exc:
            if not statusmessages:
                raise

            getSite().error_log.raising(sys.exc_info())
            IStatusMessage(getSite().REQUEST).add(
                _(u'error_while_generating_workflow',
                  default=u'${id}: Error while generating'
                  u' the workflow: ${msg}',
                  mapping={'msg': str(exc).decode('utf-8'),
                           'id': self._workflow_id(specification_path)}),
                type='error')
            return False

        with open(self._definition_path(specification_path), 'w+') as wf_file:
            generator.write(wf_file)

        if statusmessages:
            IStatusMessage(getSite().REQUEST).add(
                _(u'info_workflow_generated',
                  default=u'${id}: The workflow was generated to ${path}.',
                  mapping={'path': self._definition_path(specification_path),
                           'id': self._workflow_id(specification_path)}))
        return True

    def update_translations(self, specification_path, statusmessages=False):
        specification = self._get_specification(specification_path,
                                                statusmessages=statusmessages)
        if not specification:
            return False

        builder = I18nBuilder(specification_path)
        builder.generate(specification.language.code)

        if statusmessages:
            IStatusMessage(getSite().REQUEST).add(
                _(u'info_locales_updated',
                  default=u'${id}: The translations were updated in your'
                  u' locales directory. You should now run bin/i18n-build',
                  mapping={'id': self._workflow_id(specification_path)}))

        return True

    def _get_specification(self, specification_path, statusmessages=False):
        parser = getUtility(IWorkflowSpecificationParser)
        try:
            with open(specification_path) as specfile:
                return parser(specfile, path=specification_path)
        except ConflictError:
            raise
        except Exception, exc:
            if not statusmessages:
                raise

            getSite().error_log.raising(sys.exc_info())
            IStatusMessage(getSite().REQUEST).add(
                _(u'error_parsing_error',
                  default=u'${id}: The specification file could not be'
                  u' parsed: ${error}',
                  mapping={'error': str(exc).decode('utf-8'),
                           'id': self._workflow_id(specification_path)}),
                type='error')
            return None

    def _workflow_id(self, specification_path):
        return os.path.basename(os.path.dirname(specification_path))

    def _definition_path(self, specification_path):
        return os.path.join(os.path.dirname(specification_path),
                            'definition.xml')
