
.. _reporting_bugs_and_features:

**************************************
Reporting bugs and requesting features
**************************************

.. contents::
   :local:

.. _reporting_bugs:

Reporting a bug
===============

Security bugs
-------------

Ansible practices responsible disclosure - for security-related bugs, email `security@ansible.com <mailto:security@ansible.com>`_ to receive a prompt response. Do not submit a  ticket or post to any public groups.

Bugs in ansible-core
--------------------

Before reporting a bug, use the GitHub issue search to check `already reported issues <https://github.com/ansible/ansible/issues>`_. Unsure if you found a bug? Report the behavior on the :ref:`mailing list or community chat first <communication>`.

Also, use the mailing list or chat to discuss whether the problem is in ``ansible-core`` or a collection, and for "how do I do this" type questions.

You need a free GitHub account to `report bugs <https://github.com/ansible/ansible/issues>`_ that affects:

- multiple plugins  
- a plugin that remained in the ansible/ansible repo  
- the overall functioning of Ansible  

How to write a good bug report
------------------------------

If you find a bug, open an issue using the `issue template <https://github.com/ansible/ansible/issues/new?assignees=&labels=&template=bug_report.yml>`_. 

Fill out the issue template as completely and as accurately as possible, include:

  * your Ansible version
  * the expected behavior
  * the current behavior and why you think it is a bug
  * what you've tried including the exact commands you were using or tasks you are running
  * any relevant configurations and the components you used
  * ``ansible -vvvv`` (debugging) output
  * the steps to reproduce the bug  
    * Use a minimal reproducible example and comments describing examples
    * Preserve formatting using `code blocks  <https://help.github.com/articles/creating-and-highlighting-code-blocks/>`_ when sharing YAML in playbooks.

For multiple-file content, use gist.github.com, which is more durable than pastebin content.

.. _request_features:

Requesting a feature
====================

Before you request a feature, check what is :ref:`planned for future Ansible Releases <roadmaps>`. Check `existing pull requests tagged with feature <https://github.com/ansible/ansible/issues?q=is%3Aissue+is%3Aopen+label%3Afeature>`_.

To get your feature into Ansible, :ref:`submit a pull request <community_pull_requests>`, either against ansible-core or a collection. See also :ref:`ansible_collection_merge_requirements`. For ``ansible-core``, you can also open an issue in `ansible/ansible <https://github.com/ansible/ansible/issues>`_  or in a corresponding collection repository (To find the correct issue tracker, refer to :ref:`Bugs in collections<reporting_bugs_in_collections>` ).
