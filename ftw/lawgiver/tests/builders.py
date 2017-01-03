from ftw.builder import Builder
from ftw.builder import builder_registry
from ftw.lawgiver.tests.helpers import EXAMPLE_WF_DEF
from ftw.lawgiver.tests.helpers import EXAMPLE_WF_SPEC
from ftw.lawgiver.tests.helpers import EXAMPLE_WORKFLOW_DIR


class PackageWithWorkflowBuilder(object):

    def __init__(self, session):
        self.session = session
        self.profile_builder = (
            Builder('genericsetup profile')
            .with_file(
                'workflows/{}/specification.txt'.format(
                    EXAMPLE_WORKFLOW_DIR.name),
                EXAMPLE_WF_SPEC.bytes(),
                makedirs=True)
            .with_file(
                'workflows/{}/definition.xml'.format(
                    EXAMPLE_WORKFLOW_DIR.name),
                EXAMPLE_WF_DEF.bytes(),
                makedirs=True))

        self.package_builder = (
            Builder('python package')
            .named('the.package')
            .with_profile(self.profile_builder)
            .with_directory('locales/de/LC_MESSAGES')
            .with_directory('upgrades'))

    def with_layer(self, layer):
        self.package_builder.at_path(layer['temp_directory'])
        return self

    def create(self, **kwargs):
        return self.package_builder.create(**kwargs)


builder_registry.register('package with workflow', PackageWithWorkflowBuilder)
