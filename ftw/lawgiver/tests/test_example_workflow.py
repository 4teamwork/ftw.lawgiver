from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import WorkflowTest


class TestExampleWorkflow(WorkflowTest):

    workflow_path = 'assets/example'
    layer = LAWGIVER_INTEGRATION_TESTING
