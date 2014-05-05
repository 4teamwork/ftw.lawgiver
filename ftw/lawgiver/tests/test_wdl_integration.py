from ftw.lawgiver.testing import ZCML_FIXTURE
from ftw.lawgiver.wdl.interfaces import IWorkflowSpecificationParser
from ftw.testing import MockTestCase
from zope.component import getUtility
import os


class TestExampleSpecification(MockTestCase):

    layer = ZCML_FIXTURE

    def setUp(self):
        super(TestExampleSpecification, self).setUp()
        path = os.path.join(os.path.dirname(__file__),
                            'assets', 'example.specification.txt')
        parser = getUtility(IWorkflowSpecificationParser)

        with open(path) as file_:
            self.spec = parser(file_, path=path)

    def test_title(self):
        self.assertEquals('My Custom Workflow', self.spec.title)

    def test_description(self):
        self.assertEquals('A three state publication workflow',
                          self.spec.description)

    def test_states(self):
        self.assertEquals(
            {'Private': u'<Status "Private">',
             'Pending': u'<Status "Pending">',
             'Published': u'<Status "Published">'},

            dict(map(lambda item: (item[0], unicode(item[1])),
                     self.spec.states.items())))

    def test_private_statements(self):
        private = self.spec.states['Private']

        self.assertEquals(
            [('edit\xc3\xb6r', 'view'),
             ('edit\xc3\xb6r', 'edit'),
             ('edit\xc3\xb6r', 'delete'),
             ('edit\xc3\xb6r', 'add'),
             ('edit\xc3\xb6r', 'submit for publication'),
             ('editor-in-chief', 'view'),
             ('editor-in-chief', 'edit'),
             ('editor-in-chief', 'delete'),
             ('editor-in-chief', 'add'),
             ('editor-in-chief', 'publish')],

            private.statements)

    def test_private_worklist_viewers(self):
        pending = self.spec.states['Private']

        self.assertEquals(
            [],

            pending.worklist_viewers)

    def test_pending_statements(self):
        pending = self.spec.states['Pending']

        self.assertEquals(
            [('edit\xc3\xb6r', 'view'),
             ('edit\xc3\xb6r', 'add'),
             ('edit\xc3\xb6r', 'retract'),
             ('editor-in-chief', 'view'),
             ('editor-in-chief', 'edit'),
             ('editor-in-chief', 'delete'),
             ('editor-in-chief', 'add'),
             ('editor-in-chief', 'publish'),
             ('editor-in-chief', 'reject')],

            pending.statements)

    def test_pending_worklist_viewers(self):
        pending = self.spec.states['Pending']

        self.assertEquals(
            ['editor-in-chief'],

            pending.worklist_viewers)

    def test_published_statements(self):
        published = self.spec.states['Published']

        self.assertEquals(
            [('edit\xc3\xb6r', 'view'),
             ('edit\xc3\xb6r', 'add'),
             ('edit\xc3\xb6r', 'retract'),
             ('editor-in-chief', 'view'),
             ('editor-in-chief', 'add'),
             ('editor-in-chief', 'retract'),
             ('everyone', 'view')],

            published.statements)

    def test_published_worklist_viewers(self):
        pending = self.spec.states['Published']

        self.assertEquals(
            [],

            pending.worklist_viewers)

    def test_initial_state(self):
        self.assertEquals(self.spec.states['Private'],
                          self.spec.get_initial_status(),
                          'Wrong initial status')

    def test_transitions(self):
        self.assertEquals(
            set(['<Transition "publish" ["Private" => "Published"]>',
                 '<Transition "submit for publication" ["Private" => "Pending"]>',
                 '<Transition "reject" ["Pending" => "Private"]>',
                 '<Transition "retract" ["Pending" => "Private"]>',
                 '<Transition "publish" ["Pending" => "Published"]>',
                 '<Transition "retract" ["Published" => "Private"]>']),

            set(map(unicode, self.spec.transitions)))

    def test_role_mappings(self):
        self.assertEquals(
            {'editor-in-chief': 'Reviewer',
             'edit\xc3\xb6r': 'Editor',
             'everyone': 'Anonymous',
             'administrator': 'Site Administrator'},
            self.spec.role_mapping)

    def test_visible_roles(self):
        self.assertEquals(['edit\xc3\xb6r', 'editor-in-chief'],
                          self.spec.visible_roles)

    def test_general_statements(self):
        self.assertEquals(
            [('administrator', 'view'),
             ('administrator', 'edit'),
             ('administrator', 'delete'),
             ('administrator', 'publish')],

            self.spec.generals)
