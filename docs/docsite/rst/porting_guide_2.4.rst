.. _porting_2.4_guide:

*************************
Ansible 2.4 Porting Guide
*************************

This section discusses the behavioral changes between Ansible 2.3 and Ansible 2.4.

It is intended to assist in updating your playbooks, plugins and other parts of your Ansible infrastructure so they will work with this version of Ansible.


We suggest you read this page along with `Ansible Changelog <https://github.com/ansible/ansible/blob/devel/CHANGELOG.md#2.4>`_ to understand what updates you may need to make.

This document is part of a collection on porting. The complete list of porting guides can be found at :ref:`porting guides <porting_guides>`.

.. contents:: Topics

Playbook
========

`import_` and `include_` split
------------------------------


**OLD** In Ansible 2.3:

.. code-block:: yaml

    - name: old foo

Will result in:

.. code-block:: yaml

   [WARNING]: deprecation message 1
   [WARNING]: deprecation message 2
   [WARNING]: deprecation message 3


**NEW** In Ansible 2.4:


.. code-block:: yaml

   - name: foo

ansible_facts namespacing
-------------------------

FIXME:

Inventory plugins
-----------------

FIXME: starting migration from hardcoded inventory + inventory scripts. scripts will still work via script plugin but efforts will now concentrate on plugins

Multiple inventory
------------------

**NEW** In Ansible 2.4:


.. code-block:: shell

   ansible-playbook -i /path/to/inventory1, /some/other/path/inventory2


Deprecated
==========

Inventory argument
-------------------------

Use of --inventory-file is now deprecated. Use -inventory or -i.


Use of multiple tags
--------------------

Specifying ``--tags`` (or ``--skip-tags``) multiple times on the command line currently leads to the last one overriding all the previous ones. This behavior is deprecated. In the future, if you specify --tags multiple times the tags will be merged together. From now on, using ``--tags`` multiple times on one command line will emit a deprecation warning. Setting the ``merge_multiple_cli_tags`` option to True in the ``ansible.cfg`` file will enable the new behavior.

In 2.4, the default has change to merge the tags. You can enable the old overwriting behavior via the config option.

In 2.5, multiple ``--tags`` options will be merged with no way to go back to the old behavior.


Other caveats
-------------

Modules
=======

Major changes in popular modules are detailed here


Modules removed
---------------

The following modules no longer exist:

* None

Deprecation notices
-------------------

The following modules will be removed in Ansible 2.8. Please update update your playbooks accordingly.

* :ref:`fixme <fixme>`

Noteworthy module changes
-------------------------

Plugins
=======

var plugin changes
------------------

FIXME: bcoca to add details


Porting custom scripts
======================

Inventory script now obsolete
-----------------------------

FIXME: inventory scripts are becoming obsolete, in favor of inventory plugins

Networking
==========

There have been a number of changes to how Networking Modules operate.

Playbooks should still use ``connection: local``.

The following changes apply to:

* FIXME List modules that have been ported to new framework in 2.4 - Link back to 2.3 porting guide
