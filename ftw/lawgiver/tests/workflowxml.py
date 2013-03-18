from ftw.lawgiver.variables import VARIABLES

STANDALONE_end = '/>'
NONSTANDALONE_end = '>\n'
SUBCONTENT = '%%s'

WORKFLOW = '''<?xml version="1.0"?>
<dc-workflow workflow_id="%(id)s"
             title="%(title)s"
             description="%(description)s"
             state_variable="review_state"
             initial_state="%(initial_status)s"
             manager_bypass="False">
%%s
%---VARIABLES---%
</dc-workflow>
'''.replace('%---VARIABLES---%', VARIABLES)

STATUS_start = '\n<state state_id="%(id)s" title="%(title)s"'
STATUS_end = '\n</state>\n\n'
STATUS = STATUS_start + NONSTANDALONE_end + SUBCONTENT + STATUS_end
STATUS_STANDALONE = STATUS_start + STANDALONE_end

EXIT_TRANSITION = '<exit-transition transition_id="%s"/>'

PERMISSION_MAP = '''
        <permission-map name="%s" acquired="False">
            %%s
        </permission-map>
'''

PERMISSION_ROLE = '''
<permission-role>%s</permission-role>
'''


TRANSITION = '''
<transition transition_id="%(id)s"
            title="%(title)s"
            new_state="%(target_state)s"
            trigger="USER"
            before_script=""
            after_script="">

  <action url="%%(content_url)s/content_status_modify?workflow_action=%(id)s"
          category="workflow"
          icon="">%(title)s</action>
  %(guards)s
</transition>

'''

GUARDS = '<guard>%s</guard>'
GUARD_ROLE = '<guard-role>%s</guard-role>'
