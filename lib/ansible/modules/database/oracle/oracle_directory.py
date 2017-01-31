#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = '''
---
module: oracle_directory
short_description: Manage Oracle DB directories
description:
- Create, update or delete Oracle directories.
options:
  name:
    description:
    - Directory name like in DBA_DIRECTORIES.DIRECTORY_NAME.
    required: true
  path:
    description:
    - Directory path like in DBA_DIRECTORIES.DIRECTORY_PATH.
    - Parameter is case sensitive!
    required: false
    default: None
  state:
    description:
    - Directory state
    required: false
    default: present
    choices: ["present", "absent"]
  oracle_host:
    description:
    - Hostname or IP address of Oracle DB
    required: False
    default: 127.0.0.1
  oracle_port:
    description:
    - Listener Port
    required: False
    default: 1521
  oracle_user:
    description:
    - Account to connect as
    required: False
    default: SYSTEM
  oracle_pass:
    description:
    - Password to be used to authenticate.
    - Can be omitted if environment variable ORACLE_PASS is set.
    required: False
    default: None
  oracle_mode:
    description:
    - Connection mode.
    - Can be SYSDBA or SYSOPER.
    - Omit for normal connection.
    required: False
    default: None
    choices: ['SYSDBA', 'SYSOPER']
  oracle_sid:
    description:
    - SID to connect to
    required: False
    default: None
  oracle_service:
    description:
    - Service name to connect to
    required: False
    default: None
requirements:
- cx_Oracle
version_added: "2.3"
author: "Thomas Krahn (@nosmoht)"
'''

EXAMPLES = '''
- name: Ensure directory
  oracle_directory:
    name: DATA_PUMP_DIR
    path: /u01/app/oracle/admin/ORCL/dpdump
    oracle_host: db.example.com
    oracle_port: 1521
    oracle_user: system
    oracle_pass: manager
    oracle_sid: ORCL
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.oracle import OracleClient, HAS_ORACLE_LIB


class OracleDirectoryClient(OracleClient):
    def __init__(self, module):
        super(OracleDirectoryClient, self).__init__(module)

    def get_directory(self, name):
        sql = 'SELECT directory_name, directory_path FROM dba_directories WHERE directory_name = :name'
        row = self.fetch_one(sql, {'name': name})
        if not row:
            return None
        return {'name': row[0], 'path': row[1]}

    def get_create_directory_sql(self, name, path):
        sql = "CREATE OR REPLACE DIRECTORY %s AS '%s'" % (name, path)
        return sql

    def get_drop_directory_sql(self, name):
        sql = 'DROP DIRECTORY %s' % (name)
        return sql


def ensure(module, client):
    name = module.params['name'].upper()
    path = module.params['path']
    state = module.params['state']
    sql = []

    dir = client.get_directory(name)

    if state == 'absent':
        if dir:
            sql.append(client.get_drop_directory_sql(name=name))
    else:
        if not dir or dir.get('path') != path:
            sql.append(client.get_create_directory_sql(name=name, path=path))

    if len(sql) > 0:
        if module.check_mode:
            module.exit_json(changed=True, sql=sql, directory=dir)
        for stmt in sql:
            client.execute_sql(stmt)
        return True, client.get_directory(name), sql
    return False, dir, sql


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            path=dict(type='str', default=None),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            oracle_host=dict(type='str', default='127.0.0.1'),
            oracle_port=dict(type='str', default='1521'),
            oracle_user=dict(type='str', default='SYSTEM'),
            oracle_mode=dict(type='str', required=None, default=None, choices=[
                'SYSDBA', 'SYSOPER']),
            oracle_pass=dict(type='str', default=None, no_log=True),
            oracle_sid=dict(type='str', default=None),
            oracle_service=dict(type='str', default=None),
        ),
        required_one_of=[['oracle_sid', 'oracle_service']],
        mutually_exclusive=[['oracle_sid', 'oracle_service']],
        supports_check_mode=True,
    )

    if not HAS_ORACLE_LIB:
        module.fail_json(msg='cx_Oracle not found. Needs to be installed. See http://cx-oracle.sourceforge.net/')

    client = OracleDirectoryClient(module)
    client.connect(host=module.params['oracle_host'],
                   port=module.params['oracle_port'],
                   user=module.params['oracle_user'],
                   password=module.params['oracle_pass'],
                   mode=module.params['oracle_mode'],
                   sid=module.params['oracle_sid'], service=module.params['oracle_service'])

    changed, directory, sql = ensure(module, client)
    module.exit_json(changed=changed, directory=directory, sql=sql)


if __name__ == '__main__':
    main()
