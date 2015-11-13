from ftw.lawgiver.interfaces import IWorkflowGenerator
from ftw.lawgiver.utils import find_egginfo
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from i18ndude.catalog import MessageCatalog
from i18ndude.catalog import POWriter
from operator import attrgetter
from path import Path
from zope.component import getUtility
import os.path


def cleanup_pofile(path):
    with open(path, 'r') as file_:
        lines = file_.read().strip().split('\n')

    with open(path, 'w') as file_:
        for line in lines:
            if line.startswith('"Language-Code:') or \
                    line.startswith('"Language-Name:'):
                continue

            if line.startswith('"Domain:'):
                continue

            file_.write(line + '\n')


class I18nBuilder(object):

    def __init__(self, specification_path):
        specification_path = os.path.abspath(specification_path)
        if not os.path.exists(specification_path):
            raise ValueError(
                'Path "{0}" does not exist.'.format(specification_path))
        self.specification_path = specification_path
        self.workflow_id = os.path.basename(os.path.dirname(
                specification_path))
        self.generator = getUtility(IWorkflowGenerator)
        self.specification = self._load_specification()

    def get_locales_directory_path(self):
        """Returns the locales directory laying next to the workflow
        definition on the file system.
        The workflow definition is expected to be somewhere within
        a "profiles" directory, which has a sibling directory "locales".
        The absolute path to this "locales" directory is returned.
        If the locales directory could not be found None is returend.
        """
        path = self.specification_path
        while True:
            path, tail = os.path.split(path)
            if path == '/':
                return None
            if tail == 'profiles':
                break

        locales_path = os.path.join(path, 'locales')
        if os.path.isdir(locales_path):
            return locales_path
        else:
            return None

    def generate(self, language_code):
        """Updates translations files.
        Use ftw.recipe.translations's bin/i18n-build to rebuild and sync
        after generating the files.

        - locales/plone.pot
        This .pot-file is meant to be merged into the regular .pot-file

        - locales/${lang}/LC_MESSAGES/plone.pot
        """
        self.generate_pot()
        self.generate_po(language_code)

    def generate_pot(self):
        pot_path = os.path.join(self.get_locales_directory_path(),
                                'plone.pot')

        self._update_message_catalog(pot_path, is_pot=True)

    def generate_po(self, language_code):
        po_path = os.path.join(self.get_locales_directory_path(),
                                language_code, 'LC_MESSAGES',
                                'plone.po')

        self._update_message_catalog(po_path)

    @property
    def relative_specification_path(self):
        if getattr(self, '_relative_specification_path', None):
            return self._relative_specification_path

        path = Path(self.specification_path)
        project_root = find_egginfo(path.parent).parent
        self._relative_specification_path = path.relpath(project_root)
        return self._relative_specification_path

    def _update_message_catalog(self, catalog_path, is_pot=False):
        if not os.path.exists(os.path.dirname(catalog_path)):
            os.makedirs(os.path.dirname(catalog_path))

        if not os.path.exists(catalog_path):
            open(catalog_path, 'w+').close()

        generator = getUtility(IWorkflowGenerator)
        translations = generator.get_translations(
            self.workflow_id, self.specification)

        catalog = MessageCatalog(filename=catalog_path)

        def is_delete_candidate(msg):
            # Lawgiver used to translate the states and transitions
            # by state- / transition-id instead of by label,
            # but Plone uses the label.
            # We therefore remove all old entries.
            if msg.msgid.startswith('{0}--STATUS--'.format(self.workflow_id)):
                return True

            if msg.msgid.startswith('{0}--TRANSITION--'.format(
                    self.workflow_id)):
                return True

            # When our spec-path is in the references of the message,
            # we treat the message as delete candiate.
            if self.relative_specification_path in msg.references:
                # Remove the reference. It will be added again if we
                # still need the message.
                msg.references.remove(self.relative_specification_path)
                return True

            return False

        delete_candidates = map(attrgetter('msgid'),
                                filter(is_delete_candidate,
                                       catalog.values()))

        for msgid, msgstr in translations.items():
            msgid = msgid.decode('utf-8').replace('"', '\\"')
            msgstr = msgstr.decode('utf-8').replace('"', '\\"')

            if msgid in delete_candidates:
                delete_candidates.remove(msgid)

            if msgid in catalog:
                msg = catalog[msgid]
                msg.msgstr = msgstr
                if self.relative_specification_path not in msg.references:
                    msg.references.append(self.relative_specification_path)

                msg.automatic_comments = filter(
                    lambda text: not text.startswith('Default: '),
                    msg.automatic_comments)
                msg.automatic_comments.append(u'Default: "{0}"'.format(msgstr))

            else:
                catalog.add(msgid, msgstr=msgstr,
                            references=[self.relative_specification_path],
                            automatic_comments=[
                                u'Default: "{0}"'.format(msgstr)])

            if is_pot:
                catalog[msgid].msgstr = u''

        for msgid in delete_candidates:
            if not catalog[msgid].references:
                del catalog[msgid]

        with open(catalog_path, 'w+') as catalog_file:
            writer = POWriter(catalog_file, catalog)
            writer.write(msgstrToComment=False, sync=True)

        cleanup_pofile(catalog_path)

    def _load_specification(self):
        if getattr(self, '_specification', None) is None:
            parser = getUtility(IWorkflowSpecificationParser)
            with open(self.specification_path) as specfile:
                self._specification = parser(specfile,
                                             path=self.specification_path)
        return self._specification
