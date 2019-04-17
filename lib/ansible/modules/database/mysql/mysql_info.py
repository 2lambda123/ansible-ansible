#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2019, Andrew Klychkov (@Andersson007) <aaklychkov@mail.ru>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = r'''
---
module: mysql_info
short_description: Gather information about MySQL servers
description:
- Gathers information about MySQL servers.
version_added: '2.9'

options:
  filter:
    description:
    - Limit the collected information by comma separated string or YAML list.
    - Allowable values are C(version), C(databases), C(settings), C(roles),
      C(slave_status), C(slave_hosts), C(master_status), C(engines).
    - By default, collects all subsets.
    - You can use '!' before value (for example, C(!settings)) to exclude it from the information.
    - If you pass including and excluding values to the filter, for example, I(filter=!settings,version),
      the excluding values, C(!settings) in this case, will be ignored.
    type: list
  login_db:
    description:
    - Database name to connect to.
    type: str
    aliases:
    - database
    - db
  config_file:
    description:
    - Specify a config (credentials) file from which user and password are to be read.
    - 'Use [client] section in the file to define the credentials.'
    type: path
    default: '~/.my.cnf'

author:
- Andrew Klychkov (@Andersson007)

extends_documentation_fragment: mysql
'''

EXAMPLES = r'''
# Display info from mysql-hosts group (using creds from ~/.my.cnf to connect):
# ansible mysql-hosts -m mysql_info

# Display only databases and roles info:
# ansible mysql-hosts -m mysql_info -a 'filter=databases,roles'

# Display only slave status:
# ansible standby -m mysql_info -a 'filter=slave_status'

# Display all info from databases group except settings:
# ansible databases -m mysql_info -a 'filter=!settings'

- name: Collect all possible information using passwordless root access
  mysql_info:
    login_user: root

- name: Get MySQL version with non-default credentials
  mysql_info:
    login_user: mysuperuser
    login_password: mysuperpass
    filter: version

- name: Collect all info except settings and roles by root
  mysql_info:
    login_user: root
    login_password: rootpass
    filter: "!settings,!roles"

- name: Collect info about databases and version using ~/.my.cnf as a credential file
  become: yes
  mysql_info:
    filter:
    - databases
    - version

- name: Collect info about databases and version using ~alice/.my.cnf as a credential file
  become: yes
  mysql_info:
    config_file: /home/alice/.my.cnf
    filter:
    - databases
'''

RETURN = r'''
version:
  description: Database server version.
  returned: always
  type: dict
  sample: { "version": { "major": 5, "minor": 5, "release": 60 } }
  contains:
    major:
      description: Major server version.
      returned: always
      type: int
      sample: 5
    minor:
      description: Minor server version.
      returned: always
      type: int
      sample: 5
    release:
      description: Release server version.
      returned: always
      type: int
      sample: 60
databases:
  description: Information about databases.
  returned: always
  type: dict
  sample:
  - { "mysql": { "size": 656594 }, "information_schema": { "size": 73728 } }
  contains:
    size:
      description: Database size in bytes.
      returned: always
      type: dict
      sample: { 'size': 656594 }
settings:
  description: Global settings (variables) information.
  returned: always
  type: dict
  sample:
  - { "innodb_open_files": 300, innodb_page_size": 16384 }
roles:
  description: Roles information.
  returned: always
  type: dict
  sample:
  - { "localhost": { "root": { "Alter_priv": "Y", "Alter_routine_priv": "Y" } } }
engines:
  description: Information about the server's storage engines.
  returned: always
  type: dict
  sample:
  - { "CSV": { "Comment": "CSV storage engine", "Savepoints": "NO", "Support": "YES", "Transactions": "NO", "XA": "NO" } }
master_status:
  description: Master status information.
  returned: if master
  type: dict
  sample:
  - { "Binlog_Do_DB": "", "Binlog_Ignore_DB": "mysql", "File": "mysql-bin.000001", "Position": 769 }
slave_status:
  description: Slave status information.
  returned: if standby
  type: dict
  sample:
  - { "192.168.1.101": { "3306": { "replication_user": { "Connect_Retry": 60, "Exec_Master_Log_Pos": 769,  "Last_Errno": 0 } } } }
slave_hosts:
  description: Slave status information.
  returned: if master
  type: dict
  sample:
  - { "2": { "Host": "", "Master_id": 1, "Port": 3306 } }
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.mysql import mysql_connect, mysql_common_argument_spec, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native


# ===========================================
# MySQL module specific support methods.
#

class MySQL_Info(object):
    '''
    If you need to add a new subset:
    1. add a new key with the same name to self.info attr in self.__init__()
    2. add a new private method to get the information
    3. add invocation of the new method to self.__collect()
    4. add info about the new subset to the DOCUMENTATION block
    5. add info about the new subset with an example to RETURN block
    '''
    def __init__(self, module, cursor):
        self.module = module
        self.cursor = cursor
        self.info = {
            'version': {},
            'databases': {},
            'settings': {},
            'engines': {},
            'roles': {},
            'master_status': {},
            'slave_hosts': {},
            'slave_status': {},
        }

    def get_info(self, filter_):
        self.__collect()

        inc_list = []
        exc_list = []

        if filter_:
            partial_info = {}

            for fi in filter_:
                if fi.lstrip('!') not in self.info:
                    self.module.warn('filter element: %s is not allowable, ignored' % fi)
                    continue

                if fi[0] == '!':
                    exc_list.append(fi.lstrip('!'))

                else:
                    inc_list.append(fi)

            if inc_list:
                for i in self.info:
                    if i in inc_list:
                        partial_info[i] = self.info[i]

            else:
                for i in self.info:
                    if i not in exc_list:
                        partial_info[i] = self.info[i]

            return partial_info

        else:
            return self.info

    def __collect(self):
        self.__get_databases()
        self.__get_global_variables()
        self.__get_engines()
        self.__get_users()
        self.__get_master_status()
        self.__get_slave_status()
        self.__get_slaves()

    def __get_engines(self):
        res = self.__exec_sql('SHOW ENGINES')

        if res:
            for line in res:
                engine = line['Engine']
                self.info['engines'][engine] = {}

                for vname, val in iteritems(line):
                    if vname != 'Engine':
                        self.info['engines'][engine][vname] = val

    def __get_global_variables(self):
        res = self.__exec_sql('SHOW GLOBAL VARIABLES')

        if res:
            for var in res:
                try:
                    var['Value'] = int(var['Value'])

                except ValueError:
                    pass

                self.info['settings'][var['Variable_name']] = var['Value']

            ver = self.info['settings']['version'].split('.')
            release = ver[2].split('-')[0]

            self.info['version'] = dict(
                major=int(ver[0]),
                minor=int(ver[1]),
                release=int(release),
            )

    def __get_master_status(self):
        res = self.__exec_sql('SHOW MASTER STATUS')
        if res:
            for line in res:
                for vname, val in iteritems(line):
                    self.info['master_status'][vname] = val

    def __get_slave_status(self):
        res = self.__exec_sql('SHOW SLAVE STATUS')
        if res:
            for line in res:
                host = line['Master_Host']
                port = line['Master_Port']
                user = line['Master_User']
                self.info['slave_status'][host] = {port: {user: {}}}

                for vname, val in iteritems(line):
                    if vname not in ('Master_Host', 'Master_Port', 'Master_User'):
                        self.info['slave_status'][host][port][user][vname] = val

    def __get_slaves(self):
        res = self.__exec_sql('SHOW SLAVE HOSTS')
        if res:
            for line in res:
                srv_id = line['Server_id']
                self.info['slave_hosts'][srv_id] = {}

                for vname, val in iteritems(line):
                    if vname != 'Server_id':
                        self.info['slave_hosts'][srv_id][vname] = val

    def __get_users(self):
        res = self.__exec_sql('SELECT * FROM mysql.user')
        if res:
            for line in res:
                host = line['Host']
                user = line['User']
                self.info['roles'][host] = {user: {}}

                for vname, val in iteritems(line):
                    if vname not in ('Host', 'User'):
                        self.info['roles'][host][user][vname] = val

    def __get_databases(self):
        query = ('SELECT table_schema AS "name", '
                 'SUM(data_length + index_length) AS "size" '
                 'FROM information_schema.TABLES GROUP BY table_schema')

        res = self.__exec_sql(query)

        if res:
            for db in res:
                self.info['databases'][db['name']] = {}

                self.info['databases'][db['name']]['size'] = int(db['size'])

    def __exec_sql(self, query, ddl=False):
        try:
            self.cursor.execute(query)

            if not ddl:
                res = self.cursor.fetchall()
                return res
            return True

        except Exception as e:
            self.module.fail_json(msg="Cannot execute SQL '%s': %s" % (query, to_native(e)))
        return False


# ===========================================
# Module execution.
#


def main():
    argument_spec = mysql_common_argument_spec()
    argument_spec.update(
        login_db=dict(type='str', aliases=['db', 'database']),
        filter=dict(type='list'),
    )

    # The module doesn't support check_mode
    # because of it doesn't change anything
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=False
    )

    db = module.params['login_db']
    connect_timeout = module.params['connect_timeout']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    ssl_cert = module.params['client_cert']
    ssl_key = module.params['client_key']
    ssl_ca = module.params['ca_cert']
    config_file = module.params['config_file']
    filter_ = module.params['filter']

    if filter_:
        filter_ = [f.strip() for f in filter_]

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)

    cursor = mysql_connect(module, login_user, login_password,
                           config_file, ssl_cert, ssl_key, ssl_ca, db,
                           connect_timeout=connect_timeout, cursor_class='DictCursor')

    ###############################
    # Create object and do main job

    mysql = MySQL_Info(module, cursor)

    module.exit_json(changed=False, **mysql.get_info(filter_))


if __name__ == '__main__':
    main()
