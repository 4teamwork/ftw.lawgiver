from ftw.lawgiver.testing import LAWGIVER_INTEGRATION_TESTING
from ftw.lawgiver.tests.base import WorkflowTest
from Products.CMFPlone.utils import getFSVersionTuple


class TestExampleWorkflow(WorkflowTest):

    layer = LAWGIVER_INTEGRATION_TESTING

    @property
    def workflow_path(self):
        plone_version = getFSVersionTuple()
        if plone_version >= (4, 3, 5):
            return 'assets/example-4.3.5'
        elif plone_version > (4, 3):
            return 'assets/example-4.3.4'
        else:
            return 'assets/example-4.2'
