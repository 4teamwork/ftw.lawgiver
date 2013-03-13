ftw.lawmaker
============

The lawmaker generates Plone workflows from a human readable specification
written in a custom DSL.


----

.. parsed-literal::

    WARNING: The implementation is not yet finished. There may be features
    documented in the readme which are not implemented at all or not working
    fully yet.

----

.. contents:: Table of Contents


Motivation
----------

Developing complex Plone workflows is getting difficult when managing lots of
permissions in many states.
It is also not easy to document the decisions made.
When later a problem occurs it is diffcult for another persons to understand
how the workflow works and why certain things are made.
Another problem is how to explain the workflow to the customer since the Zope
and Plone security system is quite complex.


How it works
------------

The lawmaker helps solving theese problems by using a domain specific language
for describing how a workflow should work.
The lawmaker then creates the workflow definition (``definition.xml``) from
this specification.
By separating the specification from the workflow definition the specificion
does not rely on certain permissions - handling the permissions is the job of
the lawmaker.

Because of this fact the workflow can easily be regenerated any time and will
handle new permissions automatically when it is regenerated (but the developer
still has to regenerate the ``definition.xml`` on permission changes and make
sure that it is properly installed with an upgrade step /
reindexing security).


Installation
------------

- Add ``ftw.lawmaker`` to your buildout configuration:

.. code:: ini

    [instance]
    eggs +=
        ftw.lawmaker

- Install the generic setup profile of ``ftw.lawmaker``.


Compatibility
-------------

Runs with `Plone <http://www.plone.org/>`_ `4.3`.


Action groups
-------------

In the specification we use action groups for describing what a user with
a role can do.
It basically groups together a bunch of permissions so that we can define
the workflow from a customer perspective rather than a developer perspective.

For example there is an ``Access`` action group which contains permissions
such as ``View`` and ``Access Contents Information``.


Registering permissions to an action group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The registration of a permission to an action group should be done in the
package where the permission is defined.
This allows to keep changes of the permissions and action group registrations
together in branches, for reviews etc.
The ``ftw.lawmaker`` assigns default Plone / Zope permissions to action groups
already.

The registration is done in ZCML.
Here is an example ``lawmaker.zcml``:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawmaker="http://namespaces.zope.org/lawmaker"
        i18n_domain="my.package">

        <include package="ftw.lawmaker" file="meta.zcml" />

        <lawmaker:map_permissions
            action_group="add content"
            permissions="my.package: Add Foo
                         my.package: Add Bar"
            />

    </configure>

By putting the ZCML in a separate ``lawmaker.zcml`` file you can define
lawmaker in your addon package without having to define a dependency to
``ftw.lawmaker`` by using ``zcml:condition`` while loading it in your default
``configure.zcml``:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:zcml="http://namespaces.zope.org/zcml"
        i18n_domain="my.package">

        <include zcml:condition="installed ftw.lawmaker" file="lawmaker.zcml" />

    </configure>


Overriding action groups
~~~~~~~~~~~~~~~~~~~~~~~~

Maybe the permission to action group mapping does not work well for a specific
workflow and you would like to change to mapping for this workflow only.

This can be easily achieved by also defining the workflow in the ZCML:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawmaker="http://namespaces.zope.org/lawmaker"
        i18n_domain="my.package">

        <include package="ftw.lawmaker" file="meta.zcml" />

        <lawmaker:map_permissions
            action_group="add content"
            permissions="my.package: Add Foo
                         my.package: Add Bar"
            workflow="my_workflow"
            />

    </configure>



The workflow specification
--------------------------

The specification is written in a plain text file (``specification.txt``) in
the same directory where the ``definition.xml`` is saved.


States and transitions
~~~~~~~~~~~~~~~~~~~~~~

The states and transitions are defined in simple lists:

.. code:: rst

    States:
    - * Private
    - Pending
    - Published

    Transitions:
    - Publish (Private => Published)
    - Submit for publication (Private => Pending)
    - Reject (Pending => Private)
    - Retract (Pending => Private)
    - Publish (Pending => Published)
    - Reject (Published => Private)

The asterisk (`*`) in the state list indicates that this state is the
initial state.
We are not using any internal ids here, but the labels that the user actually
sees - the ids are generated automatically.


Role mapping
~~~~~~~~~~~~

In Plone we have quite technical roles which may not apply for all use cases,
the customer may have own roles with other names.
Since theese roles are already well configured and have certain permissions
globally (meaning: on the plone site root level) it can cause problems when
registering new roles.
Therefore we should always try to reuse the existing roles.

Because the customer has different names for his roles we need to map the
customer roles to our technical roles:

.. code:: rst

    Role mapping:
    - editor-in-chief => Reviewer
    - editor => Editor
    - everyone => Anonymous

In our example we have only "normal" editors and an "editor-in-chief" who can
review and publish the contents.
We don't use the Contributor role since our editors can edit, add and request
a review.
Giving each user two roles (Contributor and Editor) is not good since for the
customer we only have one role, the user is just editor.


General statements
~~~~~~~~~~~~~~~~~~

Usually there are some general statements, for example that an administrator
user can always edit the contents on every state.
Such statements should not be repeated for every state but defined once as
a general statement.

An example:

.. code:: rst

    General:
    - An administrator can always view the content
    - An administrator can always edit the content
    - An administrator can always delete the content

Those general statements apply for all states.


Describing states
~~~~~~~~~~~~~~~~~

For each state we describe the things a user with a certain role can do.
We have the principal that a user / role cannot do anything by default, we
have to describe every action he can do.

.. code:: rst

    State Private
    - An editor can view the content.
    - An editor can edit the content.
    - An editor can delete the content.
    - An editor can add new content.
    - An editor can Submit for publication.
    - An editor-in-chief can view the content.
    - An editor-in-chief can edit the content.
    - An editor-in-chief can delete the content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can Publish.

    State Pending
    - An editor can view the content.
    - An editor can add new content.
    - An editor can Reject.
    - An editor-in-chief can view the content.
    - An editor-in-chief can edit the content.
    - An editor-in-chief can delete the content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can Publish.
    - An editor-in-chief can Retract.

    State Published
    - An editor can view the content.
    - An editor can add new content.
    - An editor can Reject.
    - An editor-in-chief can view the content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can Reject.
    - Everyone can view the content.


Registering a workflow sepcification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you have written your workflow specification saved for example in
``profiles/default/workflows/my_custom_workflow/specification.txt`` you ned to
tell the lawmaker where your specification is so that he can generate your
workflow.
This is done in ZCML:

.. code::xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawmaker="http://namespaces.zope.org/lawmaker"
        i18n_domain="my.package">

        <include package="ftw.lawmaker" file="meta.zcml" />

        <lawmaker:specification
            title="My Custom Workflow"
            description="A three state publication workflow"
            specification="profiles/default/workflows/my_custom_workflow/specification.txt"
            />

    </configure>


Internationalization
~~~~~~~~~~~~~~~~~~~~

The package supports internationalization and is translated to english and
german.
If you need use another language we look forward to your pull request.


Generating the workflow
-----------------------

For generating the workflow go to lawmaker control panel (in the
Plone control panel).
There you can see a list of all workflows and by selecting one you can see the
specification and the details, such as the action groups.

On this view you can generate the workflow (automatically saved in the
``definition.xml`` in the same directory as the ``specification.txt``) and you
can install the workflow / update the security.



Links
-----

- Main github project repository: https://github.com/4teamwork/ftw.lawmaker
- Issue tracker: https://github.com/4teamwork/ftw.lawmaker/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.lawmaker
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.lawmaker


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.lawmaker`` is licensed under GNU General Public License, version 2.
