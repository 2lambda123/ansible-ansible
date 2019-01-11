#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Daniele Lazzari <lazzari@mailup.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# This is a windows documentation stub. Actual code lives in the .ps1
# file of the same name.

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_mssql_query
version_added: '2.8'
short_description: invokes a query on a MSSQL Server
description:
    - Invokes a query on a MSSQL Server. This module isn't idempotent, the query will be always executed.
    - In example, if you run a query that creates a database C(CREATE DATABASE TestDb), the first time it will success
    - the second time it will fail because the database already exists.
requirements:
  - Powershell module SQLPS or Powershell module SqlServer
options:
  server_instance:
    description:
      - Name of the sql server instance to query.
        If not specified, the remote host will be used.
    type: str
  server_instance_user:
    description:
      - Name of a sql user with sufficient privileges.
    type: str
  server_instance_password:
    description:
      - Password for I(server_instance_user)
    type: str
  query:
    description:
      - Query to invoke.
    type: str
    required: yes
  query_timeout:
    description:
      - Specifies the number of seconds before the queries time out.
    default: 60
    type: int
  database:
    description:
      - database where the query has to be executed
    type: str
    default: master
author:
  - Daniele Lazzari (@dlazz)
notes:
  - If the user that runs ansible has the appropriated permission on the db,
    you don't need to set C(server_instance_user) and C(server_instance_password).
    CredSSP, Kerb with cred delgation or become must be used for implicit auth to work.
'''

EXAMPLES = r'''
---
- name: get offline databases
  win_mssql_query:
    query: "SELECT name FROM sys.databases WHERE state_desc = 'OFFLINE'"
    server_instance: "{{ sql_instance }}"
    server_instance_user: sa
    server_instance_password: "{{ sa }}"
  register: databases

- name: set database online
  win_mssql_query:
    query: "ALTER DATABASE {{ item.name }} SET ONLINE"
    server_instance: "{{ sql_instance }}"
    server_instance_user: sa
    server_instance_password: "{{ sa }}"
  when: databases.output != []
  loop: "{{ databases.output }}"

- name: create a new database
  win_mssql_query:
    query: "IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = 'TestDb') CREATE DATABASE TestDb"
    server_instance: "{{ sql_instance }}"
'''

RETURN = r'''
---
output:
  description: the query result. If the query isn't a SELECT an empty list is returned.
  returned: success
  sample: [{"name": "master"}, {"name": "tempdb"}, {"name": "model"}, {"name": "msdb"}, {"name": "mydb"}]
  type: list
query:
  description: the invoked query
  returned: fail
  sample: "SELECT name from sys.satabases"
  type: str
database:
  description: the queried database
  returned: fail
  sample: "master"
  type: str
'''
