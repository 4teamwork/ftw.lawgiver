from collections import defaultdict
from ftw.lawgiver import _
from ftw.lawgiver.exceptions import UpgradeStepCreationError
from ftw.lawgiver.i18nbuilder import I18nBuilder
from ftw.lawgiver.interfaces import IUpdater
from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.interfaces import IWorkflowSpecificationDiscovery
from ftw.lawgiver.utils import in_development
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from lxml import etree
from operator import attrgetter
from path import Path
from Products.statusmessages.interfaces import IStatusMessage
from ZODB.POSException import ConflictError
from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import implements
import os.path
import pkg_resources
import shlex
import subprocess
import sys


try:
    pkg_resources.get_distribution('ftw.upgrade')
except pkg_resources.DistributionNotFound:
    FTW_UPGRADE_INSTALLED = False
else:
    FTW_UPGRADE_INSTALLED = True
    from ftw.upgrade.directory.scaffold import UpgradeStepCreator


class StatusMessageFormatter(object):

    def __init__(self, request):
        self.request = request
        self.statusmessage = IStatusMessage(self.request)

    def __call__(self, kind, message):
        self.statusmessage.add(message, type=kind)


class ConsoleMessageFormatter(object):

    def __call__(self, kind, message):
        if kind == 'error':
            stream = sys.stderr
        else:
            stream = sys.stdout

        print >>stream, translate(message)


class Updater(object):
    implements(IUpdater)

    def update_all_specifications(self, output_formatter=None):
        discovery = getMultiAdapter((getSite(), getSite().REQUEST),
                                    IWorkflowSpecificationDiscovery)
        result = []
        for specification_path in discovery.discover():
            if not in_development(specification_path):
                if output_formatter:
                    output_formatter(
                        'warning',
                        _(u'warning_skipped_released_spec',
                          default=u'${id}: Skipping released specification.',
                          mapping={
                              'id': self._workflow_id(specification_path)}))
                continue

            self.write_workflow(specification_path,
                                output_formatter=output_formatter)
            self.update_translations(specification_path,
                                     output_formatter=output_formatter)
            result.append(specification_path)

        return result

    def update_all_specifications_with_upgrade_step(
            self, output_formatter=None):
        if not FTW_UPGRADE_INSTALLED:
            raise UpgradeStepCreationError('ftw.upgrade is not installed.')

        by_packages = defaultdict(list)
        for specification_path in self.update_all_specifications(
                output_formatter=output_formatter):
            pkg_path = (Path(specification_path)
                        .joinpath('..', '..', '..', '..', '..')
                        .abspath())
            by_packages[pkg_path].append(Path(specification_path))

        for pkg_path, spec_paths in by_packages.items():
            upgrades_path = pkg_path.joinpath('upgrades')
            if not upgrades_path.isdir():
                raise UpgradeStepCreationError('Missing folder at {!r}'.format(
                    upgrades_path))

            wf_names_by_reindex_flag = {False: [], True: []}
            upgrade_dir = (UpgradeStepCreator(upgrades_path)
                           .create('Update workflows.'))
            for spec_path in spec_paths:
                def_path = spec_path.joinpath('..', 'definition.xml').abspath()
                wf_name = spec_path.parent.name
                target_dir = upgrade_dir.joinpath('workflows', wf_name)
                target_dir.makedirs()
                def_path.copy(target_dir.joinpath('definition.xml'))
                wf_names_by_reindex_flag[
                    self._has_view_permission_changed(def_path)].append(
                        str(wf_name))

            upgrade_module = upgrade_dir.joinpath('upgrade.py')
            for flag, wf_names in wf_names_by_reindex_flag.items():
                if not wf_names:
                    continue

                upgrade_module.write_bytes(
                    upgrade_module.bytes() +
                    '        self.update_workflow_security(\n'
                    '            [\'{}\'],\n'
                    '            reindex_security={!r})\n'
                    .format(('\',\n             \'').join(wf_names),
                            flag))

    def write_workflow(self, specification_path, output_formatter=None):
        specification = self._get_specification(
            specification_path, output_formatter=output_formatter)
        if not specification:
            return False

        generator = getUtility(IWorkflowGenerator)
        try:
            generator(self._workflow_id(specification_path),
                      specification)
        except ConflictError:
            raise
        except Exception, exc:
            if not output_formatter:
                raise

            getSite().error_log.raising(sys.exc_info())
            output_formatter(
                'error',
                _(u'error_while_generating_workflow',
                  default=u'${id}: Error while generating'
                  u' the workflow: ${msg}',
                  mapping={'msg': str(exc).decode('utf-8'),
                           'id': self._workflow_id(specification_path)}))
            return False

        with open(self._definition_path(specification_path), 'w+') as wf_file:
            generator.write(wf_file)

        if output_formatter:
            output_formatter(
                'info',
                _(u'info_workflow_generated',
                  default=u'${id}: The workflow was generated to ${path}.',
                  mapping={'path': self._definition_path(specification_path),
                           'id': self._workflow_id(specification_path)}))
        return True

    def update_translations(self, specification_path, output_formatter=None):
        specification = self._get_specification(
            specification_path, output_formatter=output_formatter)
        if not specification:
            return False

        builder = I18nBuilder(specification_path)
        builder.generate(specification.language.code)

        if output_formatter:
            output_formatter(
                'info',
                _(u'info_locales_updated',
                  default=u'${id}: The translations were updated in your'
                  u' locales directory. You should now run bin/i18n-build',
                  mapping={'id': self._workflow_id(specification_path)}))

        return True

    def _get_specification(self, specification_path, output_formatter=None):
        parser = getUtility(IWorkflowSpecificationParser)
        try:
            with open(specification_path) as specfile:
                return parser(specfile, path=specification_path)
        except ConflictError:
            raise
        except Exception, exc:
            if not output_formatter:
                raise

            getSite().error_log.raising(sys.exc_info())
            output_formatter(
                'error',
                _(u'error_parsing_error',
                  default=u'${id}: The specification file could not be'
                  u' parsed: ${error}',
                  mapping={'error': str(exc).decode('utf-8'),
                           'id': self._workflow_id(specification_path)}))
            return None

    def _workflow_id(self, specification_path):
        return os.path.basename(os.path.dirname(specification_path))

    def _definition_path(self, specification_path):
        return os.path.join(os.path.dirname(specification_path),
                            'definition.xml')

    def _has_view_permission_changed(self, definition_path):
        command = 'git show HEAD:./{0}'.format(definition_path.name)
        proc = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=definition_path.parent)

        stdout, stderr = proc.communicate()
        if proc.poll():
            raise UpgradeStepCreationError(
                'Error while running {0!r}.\n{1}\n{2}'.format(
                    command, stdout, stderr))

        old_definition_xml = stdout
        new_definition_xml = definition_path.bytes()

        old_roles = self.get_view_permission_roles(old_definition_xml)
        new_roles = self.get_view_permission_roles(new_definition_xml)
        return old_roles != new_roles

    def get_view_permission_roles(self, workflow_definition):
        doc = etree.fromstring(workflow_definition)
        result = {}
        for state_tag in doc.xpath('//state'):
            result[state_tag.attrib['state_id']] = map(
                attrgetter('text'),
                state_tag.xpath(
                    'permission-map[@name="View"]/permission-role'))

        return result
