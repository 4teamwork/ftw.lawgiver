ftw.lawmaker
============

The lawmaker generates Plone workflows from a human readable specification
written in a custom DSL.


----

=========
 WARNING
=========

.. parsed-literal::

    The implementation is not yet finished. There may be features documented
    in the readme which are not implemented at all.

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
The lawmaker then creates the workflow definition (``definition.xml``) from this
specification.
By separating the specification from the workflow definition the specificion
does not rely on certain permissions - handling the permissions is the job of
the lawmaker.

Because of this fact the workflow can easily be regenerated any time and will
handle new permissions automatically when it is regenerated (but the developer
still has to regenerate the ``definition.xml`` on permission changes and make
sure that it is properly installed with an upgrade step / reindexing security).


Installation
------------

- Add ``ftw.lawmaker`` to your buildout configuration:

.. code:: ini

    [instance]
    eggs +=
        ftw.lawmaker


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

The specification is written in a plain text file (``specification.txt``) in the
same directory where the ``definition.xml`` is saved.


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






Compatibility
-------------

Runs with `Plone <http://www.plone.org/>`_ `4.3`.


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
