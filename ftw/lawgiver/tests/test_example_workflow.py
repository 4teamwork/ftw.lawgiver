from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import WorkflowTest
from ftw.lawgiver.tests.helpers import EXAMPLE_WORKFLOW_DIR
from path import Path


class TestExampleWorkflow(WorkflowTest):

    layer = LAWGIVER_INTEGRATION_TESTING

    @property
    def workflow_path(self):
        return EXAMPLE_WORKFLOW_DIR.relpath(Path(__file__).dirname())
