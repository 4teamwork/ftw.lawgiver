
# We use static workflow variables:

VARIABLES = '''
<variable variable_id="action" for_catalog="False"
          for_status="True" update_always="True">
    <description>Previous transition</description>
    <default>
        <expression>transition/getId|nothing</expression>
    </default>
    <guard/>
</variable>

<variable variable_id="actor" for_catalog="False"
          for_status="True" update_always="True">
<description
>The ID of the user who performed the previous transition</description>
    <default>
        <expression>user/getId</expression>
    </default>
    <guard/>
</variable>

<variable variable_id="comments" for_catalog="False"
          for_status="True" update_always="True">
    <description>Comment about the last transition</description>
    <default>
        <expression>python:state_change.kwargs.get('comment', '')</expression>
    </default>
    <guard/>
</variable>

<variable variable_id="review_history" for_catalog="False"
          for_status="False" update_always="False">
    <description>Provides access to workflow history</description>
    <default>
        <expression>state_change/getHistory</expression>
    </default>
    <guard>
        <guard-permission>Request review</guard-permission>
        <guard-permission>Review portal content</guard-permission>
    </guard>
</variable>

<variable variable_id="time" for_catalog="False"
          for_status="True" update_always="True">
    <description>When the previous transition was performed</description>
    <default>
        <expression>state_change/getDateTime</expression>
    </default>
    <guard/>
</variable>
'''
