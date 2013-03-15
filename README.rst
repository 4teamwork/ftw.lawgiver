ftw.lawgiver
============

ftw.lawgiver generates Plone workflows based on a human readable specification written in a custom DSL (domain specific language).


----

.. parsed-literal::

    WARNING: The implementation is not yet finished. There may be features
    documented in the readme which are not implemented at all or not working
    fully yet.

----

.. contents:: Table of Contents


Motivation
----------

Developing and maintaining complex Plone workflows is a time-consuming and cumbersome endeavor. Dozens of permissions need to be managed for different roles and different workflow states. Usually, this has to be done directly in the ZMI of Zope by selecting or unselecting thousands of checkboxes. This process has been shown to be very tedious and prone to errors. Furthermore, it is no simple task to document the workflow and the associated design decisions which led to the resulting configuration of permissions and roles. The extension or adaption of an existing workflow becomes very difficult, leading to workflows which are barely maintainable.

Another problem poses the communication between workflow integrator and customer. The security system of Zope is based on a role-based access control (RBAC) which is intrinsically complex due to its use of roles, permissions, and workflow states. Experience has shown that these security concepts can be hard to convey to customer.

How it works
------------

ftw.lawgiver helps solving these problems by using a domain specific language (DSL) for describing how a workflow should work.
The lawgiver then generates the complete workflow definition (``definition.xml``) based on this specification.
By separating this specification from the resulting workflow definition (which is in XML) the specification does not have to use permissions--handling the permissions is the job of the lawgiver.

Using the specification file the workflow can easily be regenerated at any time and will handle additional permissions automatically when regenerated. However, it is still the task of the developer to regenerate the ``definition.xml`` when more or other permissions have to be managed. He or she have to make sure that the workflow is properly installed with an upgrade step /
reindexing security.


Installation
------------

- Add ``ftw.lawgiver`` to your buildout configuration:

.. code:: ini

    [instance]
    eggs +=
        ftw.lawgiver

- Install the generic setup profile of ``ftw.lawgiver``.


Compatibility
-------------

Runs with `Plone <http://www.plone.org/>`_ `4.3`.


Action groups
-------------

In the specification we use the concept of so called action groups for describing what a role is allowed to do. It basically groups together a bunch of semantically similar Plone / Zope permissions so that we only have to define the workflow based on these action groups and not on individual permissions.

For example there is an ``Access`` action group which contains permissions
such as ``View`` and ``Access Contents Information``.


Registering permissions to an action group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The registration of a permission to an action group should be done in the
package where the permission is defined.
This allows to keep changes of the permissions and action group registrations
together in branches, for reviews etc.
ftw.lawgiver already assigns default Plone / Zope permissions to action groups.

The registration is done in ZCML.
Here is an example ``lawgiver.zcml``:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" file="meta.zcml" />

        <lawgiver:map_permissions
            action_group="add content"
            permissions="my.package: Add Foo,
                         my.package: Add Bar"
            />

    </configure>

If you define multiple permissions in the same `map_permissions` directive
make sure to separate them by comma.

By putting the ZCML in a separate ``lawgiver.zcml`` file you can define
lawgiver in your addon package without having to define a dependency to
``ftw.lawgiver`` by using ``zcml:condition`` while loading it in your default
``configure.zcml``:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:zcml="http://namespaces.zope.org/zcml"
        i18n_domain="my.package">

        <include zcml:condition="installed ftw.lawgiver" file="lawgiver.zcml" />

    </configure>


Overriding action groups
~~~~~~~~~~~~~~~~~~~~~~~~

Maybe the permission to action group mapping does not work well for a specific
workflow and you would like to change to mapping for this workflow only.

This can be easily achieved by also defining the workflow in the ZCML:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" file="meta.zcml" />

        <lawgiver:map_permissions
            action_group="add content"
            permissions="my.package: Add Foo,
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

    Title: My Custom Workflow
    Description: A three state publication workflow

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
We are not using any internal ids for workflow states or transitions. Instead, we use the same labels which the user will actually see--the ids are automatically generated by ftw.lawgiver.


Role mapping
~~~~~~~~~~~~

In Plone we have a given set of rather technical roles (e.g. Editor, Contributor, Reader) which may not apply for all use cases in real life. The customer may have own roles with different names.
Since the existing roles are already well established in Plone it is usually not a good thing to add new roles to Plone. It is better to try to reuse the existing roles.

Because the customer has different labels for his roles we need to map
customer roles to Plone roles:

.. code:: rst

    Role mapping:
    - editor-in-chief => Reviewer
    - editor => Editor
    - everyone => Anonymous

In our example we have only "normal" editors and an "editor-in-chief" who can
review and publish the contents.
We do not have to use the Contributor role since our editors can edit, add new content, and request a review for existing content. Therefore, it is not necessary to distinguish Editor and Contributor role.


General statements
~~~~~~~~~~~~~~~~~~

Usually there are some general statements, for example that a user with adminstrator role can always edit the contents on any workflow state.
Such statements should not be repeated for every state but defined once as
a general statement.

An example:

.. code:: rst

    General:
    - An administrator can always view the content
    - An administrator can always edit the content
    - An administrator can always delete the content

These general statements apply for all states.


Describing states
~~~~~~~~~~~~~~~~~

For each state we describe the actions a user with a certain role can do.
We have the principle that any user / role is NOT allowed do anything by default, we have to explicitly list every action he will be allowed to perform.

.. code:: rst

    State Private:
    - An editor can view this content.
    - An editor can edit this content.
    - An editor can delete this content.
    - An editor can add new content.
    - An editor can submit this content for publication.
    - An editor-in-chief can view this content.
    - An editor-in-chief can edit this content.
    - An editor-in-chief can delete this content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can publish this content.

    State Pending:
    - An editor can view this content.
    - An editor can add new content.
    - An editor can retract this content.
    - An editor-in-chief can view this content.
    - An editor-in-chief can edit this content.
    - An editor-in-chief can delete this content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can publish this content.
    - An editor-in-chief can reject this content.

    State Published:
    - An editor can view this content.
    - An editor can add new content.
    - An editor can retract this content.
    - An editor-in-chief can view this content.
    - An editor-in-chief can add new content.
    - An editor-in-chief can reject this content.
    - Anyone can view this content.


Registering a workflow specification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming we have a workflow specification stored in
``profiles/default/workflows/my_custom_workflow/specification.txt`` we need
to tell ftw.lawgiver where it is in order to generate the workflow XML.
This is done in ZCML:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" file="meta.zcml" />

        <lawgiver:workflows
            directory="profiles/default/workflows"
            />

    </configure>

We are registering the "workflows" directory of our generic setup profile
here.
The lawgiver now checks for every workflow in this directory whether there is
a ``specification.txt`` and registers it dynamically.


Internationalization
~~~~~~~~~~~~~~~~~~~~

The package supports internationalization and is translated to English and
German.
If you need to use another language we look forward to your pull request.


Generating the workflow
-----------------------

For generating the workflow go to the lawgiver control panel (in the
Plone control panel).
There you can see a list of all workflows and by selecting one you can see the specification and other details, such as the action groups.

On this view you can generate the workflow (automatically saved in the
``definition.xml`` in the same directory as the ``specification.txt``) and you
can install the workflow / update the security.



Links
-----

- Main github project repository: https://github.com/4teamwork/ftw.lawgiver
- Issue tracker: https://github.com/4teamwork/ftw.lawgiver/issues
- Package on pypi: http://pypi.python.org/pypi/ftw.lawgiver
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.lawgiver


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.lawgiver`` is licensed under GNU General Public License, version 2.
