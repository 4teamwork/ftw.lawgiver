ftw.lawgiver
============

``ftw.lawgiver`` generates Plone workflows based on a human readable
specification written in a custom
`DSL <http://en.wikipedia.org/wiki/Domain-specific_language>`_.

.. contents:: Table of Contents


Motivation
----------

Developing and maintaining complex Plone workflows is a time-consuming and
cumbersome endeavor. Dozens of permissions need to be managed for different
roles and different workflow states. Usually, this has to be done directly in
the ZMI of Zope by selecting or unselecting thousands of checkboxes. This
process has been shown to be very tedious and prone to errors. Furthermore, it
is no simple task to document the workflow and the associated design decisions
which led to the resulting configuration of permissions and roles. The extension
or adaption of an existing workflow becomes very difficult, leading to workflows
which are barely maintainable.

Another problem poses the communication between workflow integrator and
customer. The security system of Zope is based on a role-based access control
(RBAC) which is intrinsically complex due to its use of roles, permissions, and
workflow states. Experience has shown that these security concepts can be hard
to convey to customers.


How it works
------------

``ftw.lawgiver`` helps solving these problems by using a DSL to describe how
a workflow should work. The lawgiver then generates the complete workflow
definition (``definition.xml``) based on this specification.  By separating this
specification from the resulting workflow definition (which is in XML) the
specification does not have to use permissions--handling the permissions is the
job of the lawgiver.

Using the specification file the workflow can easily be regenerated at any time
and will handle additional permissions automatically when regenerated. However,
it is still the task of the developer to regenerate the ``definition.xml`` when
more or other permissions have to be managed. He or she have to make sure that
the workflow is properly installed with an upgrade step / reindexing security.


Installation
------------

- Add ``ftw.lawgiver`` to your buildout configuration:

.. code:: rst

    [instance]
    eggs +=
        ftw.lawgiver

- Install the generic setup profile of ``ftw.lawgiver``.


Compatibility
-------------

Plone 4.3

.. image:: https://jenkins.4teamwork.ch/job/ftw.lawgiver-master-test-plone-4.3.x.cfg/badge/icon
   :target: https://jenkins.4teamwork.ch/job/ftw.lawgiver-master-test-plone-4.3.x.cfg


Action groups
-------------

In the specification we use the concept of so called action groups for
describing what a role is allowed to do. It basically groups together a bunch of
semantically similar Plone / Zope permissions so that we only have to define the
workflow based on these action groups and not on individual permissions.

For example there is an ``Access`` action group which contains permissions such
as ``View`` and ``Access Contents Information``.


Registering permissions to an action group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The registration of a permission to an action group should be done in the
package where the permission is defined.  This allows to keep changes of the
permissions and action group registrations together in branches, for reviews
etc. ``ftw.lawgiver`` already assigns default Plone / Zope permissions to action
groups.

The registration is done in ZCML.
Here is an example ``lawgiver.zcml``:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" file="meta.zcml" />

        <lawgiver:map_permissions
            action_group="add"
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
            action_group="add"
            permissions="my.package: Add Foo,
                         my.package: Add Bar"
            workflow="my_workflow"
            />

    </configure>


Assigning permission to multiple action groups
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes, a permission should be assigned to multiple action groups.
This can be done with the ``move`` attribute of the ``map_permissions`` directive.
Just make sure that all other ``map_permissions`` ZCMLs are loaded before doing that,
especially the default ``lawgiver.zcml`` of ``ftw.lawgiver``.

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" />

        <lawgiver:map_permissions
            action_group="add"
            permissions="Add portal content"
            />

        <lawgiver:map_permissions
            action_group="add ticket"
            permissions="my.package: Add Ticket"
            workflow="my_workflow"
            />
            
        <!-- We want to have "Add portal content" in the "add ticket" action group too,
             but we should not remove it from "add".
             By using move="False" we can add "Add portal content" to "add ticket" without
             removing it from "add".
             /-->

        <lawgiver:map_permissions
            action_group="add ticket"
            permissions="Add portal content"
            workflow="my_workflow"
            move="False"
            />

    </configure>



The workflow specification
--------------------------

The specification is written in a plain text file (``specification.txt``) in
the same directory where the ``definition.xml`` is saved.

**Examples:**

- `specification.txt (English) <https://github.com/4teamwork/ftw.lawgiver/blob/master/ftw/lawgiver/tests/assets/languages/specification.txt>`_
- `specification.de.txt (German) <https://github.com/4teamwork/ftw.lawgiver/blob/master/ftw/lawgiver/tests/assets/languages/specification.de.txt>`_



States and transitions
~~~~~~~~~~~~~~~~~~~~~~

The states and transitions are defined in simple lists:

.. code:: rst

    [My Custom Workflow]
    Description: A three state publication workflow
    Initial Status: Private

    Status Private:

    Status Pending:

    Status Published:

    Transitions:
      Publish (Private => Published)
      Submit for publication (Private => Pending)
      Reject (Pending => Private)
      Retract (Pending => Private)
      Publish (Pending => Published)
      Reject (Published => Private)

We are not using any internal ids for workflow states or
transitions. Instead, we use the same labels which the user will actually
see--the ids are automatically generated by ``ftw.lawgiver``.


Role mapping
~~~~~~~~~~~~

In Plone we have a given set of rather technical roles (e.g. Editor,
Contributor, Reader) which may not apply for all use cases in real life. The
customer may have own roles with different names.  Since the existing roles are
already well established in Plone it is usually not a good thing to add new
roles to Plone. It is better to try to reuse the existing roles.

Because the customer has different labels for his roles we need to map
customer roles to Plone roles:

.. code:: rst

    Role mapping:
      editor-in-chief => Reviewer
      editor => Editor
      everyone => Anonymous

In our example we have only "normal" editors and an "editor-in-chief" who can
review and publish the contents.  We do not have to use the Contributor role
since our editors can edit, add new content, and request a review for existing
content. Therefore, it is not necessary to distinguish Editor and Contributor
role.


General statements
~~~~~~~~~~~~~~~~~~

Usually there are some general statements, for example that a user with
adminstrator role can always edit the contents on any workflow state.  Such
statements should not be repeated for every state but defined once as a general
statement.

An example:

.. code:: rst

    General:
      An administrator can always view the content
      An administrator can always edit the content
      An administrator can always delete the content

These general statements apply for all states.


Describing states
~~~~~~~~~~~~~~~~~

For each state we describe the actions a user with a certain role can do.  We
have the principle that any user / role is NOT allowed do anything by default,
we have to explicitly list every action he will be allowed to perform.

.. code:: rst

    Status Private:
      An editor can view this content.
      An editor can edit this content.
      An editor can delete this content.
      An editor can add new content.
      An editor can submit for publication.
      An editor-in-chief can view this content.
      An editor-in-chief can edit this content.
      An editor-in-chief can delete this content.
      An editor-in-chief can add new content.
      An editor-in-chief can publish this content.

    Status Pending:
      An editor can view this content.
      An editor can add new content.
      An editor can retract this content.
      An editor-in-chief can view this content.
      An editor-in-chief can edit this content.
      An editor-in-chief can delete this content.
      An editor-in-chief can add new content.
      An editor-in-chief can publish this content.
      An editor-in-chief can reject this content.

    Status Published:
      An editor can view this content.
      An editor can add new content.
      An editor can retract this content.
      An editor-in-chief can view this content.
      An editor-in-chief can add new content.
      An editor-in-chief can retract this content.
      Anyone can view this content.


Role inheritance
~~~~~~~~~~~~~~~~

Roles can be inherited from other roles, globally and for a single status:

.. code:: rst

    [Role Inheritance Workflow]
    Initial Status: Foo

    Role mapping:
      editor => Editor
      editor-in-chief => Reviewer
      administrator => Site Administrator

    General:
      An administrator can always perform the same actions as an editor.
      An administrator can always perform the same actions as an editor-in-chief.

    Status Foo:
      An editor-in-chief can perform the same actions as an editor.
      An editor can view this content.
      An editor can edit this content.

    Status Bar:
      An editor can view this content.
      An editor-in-chief can view this content.
      An editor-in-chief can edit this content.


Worklists
~~~~~~~~~

Worklists are automatically generated for you when you grant access to the
worklist:

.. code:: rst

    [A workflow]
    ...

    Status Pending:
      An editor-in-chief can access the worklist.

Those "can access the worklist" statements do not work in the "General" section,
they need to be defined a "Status" section.

For each status with "can access the worklist" statements a worklist is
generated, guarded with the role for which there is a statement.


Workflow specification discovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All workflow directories in registered generic setup profiles
are automatically scanned for workflow specifications.
Just place a ``specification.txt`` in a workflow directory and ``ftw.lawgiver``
will discover it automatically.

Example paths:

- Specification: ``profiles/default/workflows/my_custom_workflow/specification.txt``
- Workflow XML: ``profiles/default/workflows/my_custom_workflow/definition.txt``

In this example it is assumed that ``profiles/default`` is a registered generic setup
profile directory.


Changing Transition URLs
~~~~~~~~~~~~~~~~~~~~~~~~

Sometimes the transition URLs need to point to another view.  This can be
achieved by using the `transition-url` option, where a string can be passed
which will then be substituted with the `transition` id.  Be sure to use a
double `%%` for parts which should not be replaced when generating the workflow,
such as the `%%(content_url)s`.

Example:

.. code:: rst

    transition-url = %%(content_url)s/custom_wf_action?workflow_action=%(transition)s



Languages
~~~~~~~~~

Currently supported languages:

**English** (default)

- Filename: ``specification.txt``
- Example: `ftw/lawgiver/tests/assets/languages/specification.txt <https://github.com/4teamwork/ftw.lawgiver/blob/master/ftw/lawgiver/tests/assets/languages/specification.txt>`_

**German**

- Filename: ``specification.de.txt``
- Example: `ftw/lawgiver/tests/assets/languages/specification.de.txt <https://github.com/4teamwork/ftw.lawgiver/blob/master/ftw/lawgiver/tests/assets/languages/specification.de.txt>`_


**Contributing new languages**

We happily accept pull requests with new languages!

Creating a new language is as simple:

- Create a new specification example in ``ftw/lawgiver/tests/assets/languages/``,
  implementing the same workflow as ``specification.txt``.
- Run the tests with ``bin/test``. It should fail at this point. Keep running them
  after each change.
- Add a new language module to ``ftw/lawgiver/wdl/languages/``.
- Register the new language in ``ftw/lawgiver/wdl/languages/__init__.py``.
- Implement the language specific constraints and extraction methods in your new
  language class until all tests pass.
- Add the language to the readme.
- Send us a pull request!




Generating the workflow
-----------------------

For generating the workflow go to the lawgiver control panel (in the Plone
control panel). There you can see a list of all workflows and by selecting one
you can see the specification and other details, such as the action groups.

On this view you can generate the workflow (automatically saved in the
``definition.xml`` in the same directory as the ``specification.txt``) and you
can install the workflow / update the security.

.. image:: https://raw.github.com/4teamwork/ftw.lawgiver/master/docs/screenshot-workflow-details.png


Updating translations
~~~~~~~~~~~~~~~~~~~~~

The button ``Update translations in locales directory`` in the workflow
details view helps you keep your translations up to date.
It writes directly into the locales directory on your machine.

When updating the translations, theese files are written:

- ``your/package/locales/plone.pot``
- ``your/package/locales/en/LC_MESSAGES/plone.po``

When updating the messages in your locales file, all no longer valid messages
which start with the workflow ID prefix are removed automatically.



Testing the workflow
--------------------

It is important to detect when you have to rebuild your workflow.
It is also important to dected permissions from third party addons which
are not yet mapped to action groups.

By subclassing the `WorkflowTest` it is easy to write a test for your
workflow:

.. code:: python

    from ftw.lawgiver.tests.base import WorkflowTest
    from my.package.testing import MY_INTEGRATION_TESTING


    class TestMyWorkflow(WorkflowTest):

        # The workflow path may be a path relative to the this file or
        # an absolute path.
        workflow_path = '../profiles/default/workflows/my-workflow'

        # Use an integration testing layer.
        layer = MY_INTEGRATION_TESTING

What is tested?

- The test will fail when your workflow (`definition.xml`) needs to be
  regenerated. This may be because new permissions should be managed.

- The test will fail when you install new addons which provide new
  permissions. The permissions should be mapped to action groups or marked
  as unmanaged explicitly:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="ftw.lawgiver">

        <include package="ftw.lawgiver" file="meta.zcml" />


        <lawgiver:ignore
            workflow="my_workflow"
            permissions="ATContentTypes: Upload via url,
                         ATContentTypes: View history"
            />

    </configure>


Customizing the sharing view
----------------------------

Lawgiver allows you to customize the sharing view to your needs.


Roles in sharing view
~~~~~~~~~~~~~~~~~~~~~

By default the ``@@sharing`` view lists some default Plone roles:

- Can add (`Contributor`)
- Can edit (`Editor`)
- Can review (`Reviewer`)
- Can view (`Reader`)

Often the workflow does not use all of those roles, or uses different ones.
Lawgiver allows you to configure which roles are showing up in at the ``sharing``
view. If your users are granting roles on the ``@@sharing`` view, you should probably
configure the roles so that they have meanigful names and only the relevant ones
are listed.

If you want to customize the displayed roles for your workflow, you
can do this right in your workflow specification:

.. code:: rst

    [A workflow]

    Role mapping:
      editor => Editor
      editor-in-chief => Reviewer
      administrator => Site Administrator

    Visible roles:
      editor
      editor-in-chief

The lawgiver then sets the permissions required for managing a role correctly.
This works for registered roles. Plone only registers `Contributor`, `Editor`,
`Reviewer` and `Reader` by default.
See the `Registering additional roles`_ section.


Translating the roles
~~~~~~~~~~~~~~~~~~~~~

The lawgiver extends Plone's role translation system so that the
roles in the ``@@sharing`` view can be translated per workflow.

This is done through the Plone standard role utilites, allowing addon
tools to also use the corrent role translation without the need of
customization.

The lawgiver provides example translations (`plone.pot` / `plone.po`) in
the lawgiver control panel, which can easily be copied to your local plone
translations (`locales`). Theese translations also include role translations
and can be modified when in need.

The lawgiver automatically looks up the right translation of the roles, depending
on your workflow.


Registering additional roles
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can easily register custom roles or Plone default roles which are not visible
by default (such as `Site Manager`).

Use the lawgiver directive for registering new roles:

.. code:: xml

    <configure
        xmlns="http://namespaces.zope.org/zope"
        xmlns:lawgiver="http://namespaces.zope.org/lawgiver"
        i18n_domain="my.package">

        <include package="ftw.lawgiver" file="meta.zcml" />

        <lawgiver:role name="Site Manager" />

    </configure>

The `lawgiver:role` directive does all the required things for you, such as
registering the permission in zope, mapping the permission to the default
lawgiver `manage security` action group and registering the required utility
and adapter.

Optional arguments:

- ``permission``: the required permission for granting this role. The permission
  is automatically generated as ``Sharing page: Delegate [ROLE] role``.

- ``register_permission``: automatically registers the permissions in Zope. This
  is ``True`` by default.

- ``map_permission``: automatically map the permission to the default lawgiver
  ``manage security`` action group. Lawgiver will also re-map the permission
  according to your ``Visible roles`` configuration in the workflow specification.


Description of roles in sharing view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``ftw.lawgiver`` automatically registers an overlay when clicking on the
role text in the table header on the sharing view.
The overlay displays a description of what this role can do in each state of
the current workflow:


.. image:: https://raw.github.com/4teamwork/ftw.lawgiver/master/docs/screenshot-sharing-overlay.png


Adding text to the overlay
++++++++++++++++++++++++++

You can add text to the overlay per role directly in your workflow specification:


.. code:: rst

    [A workflow]

    Role mapping:
      editor => Editor
      editor-in-chief => Reviewer
      administrator => Site Administrator

    editor-in-chief role description:
      The editor-in-chief reviews and publishes content.

This text is included as translation proposal for the ``plone`` domain, which
makes it easy to translate it to other languages for multilingual sites.



Specialities
------------

Deleting content
~~~~~~~~~~~~~~~~

The ``ftw.lawgiver`` uses `collective.deletepermission`_.  If you generate a
workflow using lawgiver and install it in production without lawgiver, be sure
to install `collective.deletepermission`_!

`collective.deletepermission`_ solves a delete problem which occurs in certain
situations by adding a new delete permission. See its readme for further
details.

For beeing able to delete a content, the user should have the "delete" action
group (`Delete portal content`) on the content but also "add" (`Delete objects`)
on the parent content



Uninstall
---------

This package provides an uninstall Generic Setup profile, however, it will
not uninstall the package dependencies.
Make sure to uninstall the dependencies if you no longer use them.


Rebuild with console
--------------------

``ftw.lawgiver`` registers a zopectl command so that all workflows can be
rebuilt at once using the console::

  $ ./bin/instance rebuild_workflows --help
  usage: interpreter [-h] [-s SITE]

  Rebuild ftw.lawgiver workflows.

  optional arguments:
    -h, --help            show this help message and exit
    -s SITE, --site SITE  Path to the Plone site for discovering the worklfows.
                          (default: Plone)


Links
-----

- Github: https://github.com/4teamwork/ftw.lawgiver
- Issues: https://github.com/4teamwork/ftw.lawgiver/issues
- Pypi: http://pypi.python.org/pypi/ftw.lawgiver
- Continuous integration: https://jenkins.4teamwork.ch/search?q=ftw.lawgiver


Copyright
---------

This package is copyright by `4teamwork <http://www.4teamwork.ch/>`_.

``ftw.lawgiver`` is licensed under GNU General Public License, version 2.

.. _collective.deletepermission: https://github.com/4teamwork/collective.deletepermission
.. _ftw.recipe.translations: https://github.com/4teamwork/ftw.recipe.translations
