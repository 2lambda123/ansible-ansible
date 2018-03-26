#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Mark Theunissen <mark.theunissen@gmail.com>
# Sponsored by Four Kitchens http://fourkitchens.com.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = r'''
---
module: mysql_user
short_description: Adds or removes a user from a MySQL database
description:
   - Adds or removes a user from a MySQL database.
version_added: "0.6"
options:
  name:
    description:
      - Name of the user (role) to add or remove.
    type: str
    required: true
  password:
    description:
      - Set the user's password..
    type: str
    required: false
    default: null
  require_ssl:
    description:
      - require the user to login with ssl enabled.
      - replaces the old special privilege REQUIRESSL.
      - introduced to allow compatibility with MySQL > 5.7.6
      - introduced to allow compatibility with MariaDB > 10.2.0
    type: bool
    required: false
    default: "no"
    version_added: "2.6"
  encrypted:
    description:
      - Indicate that the 'password' field is a `mysql_native_password` hash.
    type: bool
    default: no
    version_added: "2.0"
  host:
    description:
      - The 'host' part of the MySQL username.
    type: str
    default: localhost
  host_all:
    description:
      - Override the host option, making ansible apply changes to all hostnames for a given user.
      - This option cannot be used when creating users.
    type: bool
    default: no
    version_added: "2.1"
  priv:
    description:
      - "MySQL privileges string in the format: C(db.table:priv1,priv2)."
      - "Multiple privileges can be specified by separating each one using
        a forward slash: C(db.table:priv/db.table:priv)."
      - The format is based on MySQL C(GRANT) statement.
      - Database and table names can be quoted, MySQL-style.
      - If column privileges are used, the C(priv1,priv2) part must be
        exactly as returned by a C(SHOW GRANT) statement. If not followed,
        the module will always report changes. It includes grouping columns
        by permission (C(SELECT(col1,col2)) instead of C(SELECT(col1),SELECT(col2))).
    type: str
  append_privs:
    description:
      - Append the privileges defined by priv to the existing ones for this
        user instead of overwriting existing ones.
    type: bool
    default: no
    version_added: "1.4"
  sql_log_bin:
    description:
      - Whether binary logging should be enabled or disabled for the connection.
    type: bool
    default: yes
    version_added: "2.1"
  state:
    description:
      - Whether the user should exist.
      - When C(absent), removes the user.
    type: str
    choices: [ absent, present ]
    default: present
  check_implicit_admin:
    description:
      - Check if mysql allows login as root/nopassword before trying supplied credentials.
    type: bool
    default: no
    version_added: "1.3"
  update_password:
    description:
      - C(always) will update passwords if they differ.
      - C(on_create) will only set the password for newly created users.
    type: str
    choices: [ always, on_create ]
    default: always
    version_added: "2.0"
notes:
   - "MySQL server installs with default login_user of 'root' and no password. To secure this user
     as part of an idempotent playbook, you must create at least two tasks: the first must change the root user's password,
     without providing any login_user/login_password details. The second must drop a ~/.my.cnf file containing
     the new root credentials. Subsequent runs of the playbook will then succeed by reading the new credentials from
     the file."
   - Currently, there is only support for the `mysql_native_password` encrypted password hash module.

author:
- Jonathan Mainguy (@Jmainguy)
extends_documentation_fragment: mysql
'''

EXAMPLES = r'''
- name: Removes anonymous user account for localhost
  mysql_user:
    name: ''
    host: localhost
    state: absent

- name: Removes all anonymous user accounts
  mysql_user:
    name: ''
    host_all: yes
    state: absent

- name: Create database user with name 'bob' and password '12345' with all database privileges
  mysql_user:
    name: bob
    password: 12345
    priv: '*.*:ALL'
    state: present

- name: Create database user using hashed password with all database privileges
  mysql_user:
    name: bob
    password: '*EE0D72C1085C46C5278932678FBE2C6A782821B4'
    encrypted: yes
    priv: '*.*:ALL'
    state: present

- name: Create database user with password and all database privileges and 'WITH GRANT OPTION'
  mysql_user:
    name: bob
    password: 12345
    priv: '*.*:ALL,GRANT'
    state: present

<<<<<<< HEAD
# Note that REQUIRESSL is a special privilege that should only apply to *.* by itself.
- name: Modify user to require SSL connections.
  mysql_user:
    name: bob
    append_privs: yes
    priv: '*.*:REQUIRESSL'
    state: present

- name: Ensure no user named 'sally'@'localhost' exists, also passing in the auth credentials.
  mysql_user:
=======
# Ensure no user named 'sally'@'localhost' exists, also passing in the auth credentials.
- mysql_user:
>>>>>>> Make `mysql_user` idempotent with regards to SSL
    login_user: root
    login_password: 123456
    name: sally
    state: absent

- name: Ensure no user named 'sally' exists at all
  mysql_user:
    name: sally
    host_all: yes
    state: absent

- name: Specify grants composed of more than one word
  mysql_user:
    name: replication
    password: 12345
    priv: "*.*:REPLICATION CLIENT"
    state: present

- name: Revoke all privileges for user 'bob' and password '12345'
  mysql_user:
    name: bob
    password: 12345
    priv: "*.*:USAGE"
    state: present

# Example privileges string format
# mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanotherdb.*:ALL

- name: Example using login_unix_socket to connect to server
  mysql_user:
    name: root
    password: abc123
    login_unix_socket: /var/run/mysqld/mysqld.sock

- name: Example of skipping binary logging while adding user 'bob'
  mysql_user:
    name: bob
    password: 12345
    priv: "*.*:USAGE"
    state: present
    sql_log_bin: no

# Example .my.cnf file for setting the root password
# [client]
# user=root
# password=n<_665{vS43y
'''

import re
import string

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.database import SQLParseError
from ansible.module_utils.mysql import mysql_connect, mysql_driver, mysql_driver_fail_msg
from ansible.module_utils.six import iteritems
from ansible.module_utils._text import to_native
from distutils.version import LooseVersion

VALID_PRIVS = frozenset(('CREATE', 'DROP', 'GRANT', 'GRANT OPTION',
                         'LOCK TABLES', 'REFERENCES', 'EVENT', 'ALTER',
                         'DELETE', 'INDEX', 'INSERT', 'SELECT', 'UPDATE',
                         'CREATE TEMPORARY TABLES', 'TRIGGER', 'CREATE VIEW',
                         'SHOW VIEW', 'ALTER ROUTINE', 'CREATE ROUTINE',
                         'EXECUTE', 'FILE', 'CREATE TABLESPACE', 'CREATE USER',
                         'PROCESS', 'PROXY', 'RELOAD', 'REPLICATION CLIENT',
                         'REPLICATION SLAVE', 'SHOW DATABASES', 'SHUTDOWN',
                         'SUPER', 'ALL', 'ALL PRIVILEGES', 'USAGE', 'REQUIRESSL',
                         'CREATE ROLE', 'DROP ROLE', 'APPLICATION PASSWORD ADMIN',
                         'AUDIT ADMIN', 'BACKUP ADMIN', 'BINLOG ADMIN',
                         'BINLOG ENCRYPTION ADMIN', 'CONNECTION ADMIN',
                         'ENCRYPTION KEY ADMIN', 'FIREWALL ADMIN', 'FIREWALL USER',
                         'GROUP REPLICATION ADMIN', 'PERSIST RO VARIABLES ADMIN',
                         'REPLICATION SLAVE ADMIN', 'RESOURCE GROUP ADMIN',
                         'RESOURCE GROUP USER', 'ROLE ADMIN', 'SET USER ID',
                         'SESSION VARIABLES ADMIN', 'SYSTEM VARIABLES ADMIN',
                         'VERSION TOKEN ADMIN', 'XA RECOVER ADMIN'))


class InvalidPrivsError(Exception):
    pass


# ===========================================
# MySQL module specific support methods.
#


# User Authentication Management was changed in MySQL 5.7.6 and MariaDB 10.2.0.
# This is a check to verify whether old or new style needs to be used.
def use_user_for_non_privilege_actions(cursor):
    cursor.execute("SELECT VERSION()")
    result = cursor.fetchone()
    version_signature = result[0]

    # MariaDB version looks like: 10.0.3-MariaDB-1~precise-log
    # MySQL version looks like 5.6.10
    if 'mariadb' in version_signature.lower():
        return False
    else:
        return LooseVersion(version_signature) >= LooseVersion('5.7.6')


def get_mode(cursor):
    cursor.execute('SELECT @@GLOBAL.sql_mode')
    result = cursor.fetchone()
    mode_str = result[0]
    if 'ANSI' in mode_str:
        mode = 'ANSI'
    else:
        mode = 'NOTANSI'
    return mode


def user_exists(cursor, user, host, host_all):
    if host_all:
        cursor.execute("SELECT count(*) FROM user WHERE user = %s", ([user]))
    else:
        cursor.execute("SELECT count(*) FROM user WHERE user = %s AND host = %s", (user, host))

    count = cursor.fetchone()
    return count[0] > 0


def user_add(cursor, user, host, host_all, password, encrypted, new_priv, require_ssl, check_mode):
    # we cannot create users without a proper hostname
    if host_all:
        return False

    if check_mode:
        return True

    if password and encrypted:
        cursor.execute("CREATE USER %s@%s IDENTIFIED BY PASSWORD %s", (user, host, password))
    elif password and not encrypted:
        cursor.execute("CREATE USER %s@%s IDENTIFIED BY %s", (user, host, password))
    else:
        cursor.execute("CREATE USER %s@%s", (user, host))
    if new_priv is not None:
        for db_table, priv in iteritems(new_priv):
            privileges_grant(cursor, user, host, db_table, priv)

    if require_ssl:
        use_user_for_non_priv = use_user_for_non_privilege_actions(cursor)
        user_set_require_ssl(cursor, user, host, use_user_for_non_priv)

    return True


def is_hash(password):
    ishash = False
    if len(password) == 41 and password[0] == '*':
        if frozenset(password[1:]).issubset(string.hexdigits):
            ishash = True
    return ishash


def user_mod(cursor, user, host, host_all, password, encrypted, new_priv, new_require_ssl, append_privs, module):
    changed = False
    grant_option = False

    if host_all:
        hostnames = user_get_hostnames(cursor, [user])
    else:
        hostnames = [host]

    for host in hostnames:
        use_user_for_non_priv = use_user_for_non_privilege_actions(cursor)

        # Handle clear text and hashed passwords.
        if bool(password):
            if not use_user_for_non_priv:
                cursor.execute("SELECT password FROM user WHERE user = %s AND host = %s", (user, host))
            else:
                cursor.execute("SELECT authentication_string FROM user WHERE user = %s AND host = %s", (user, host))
            current_pass_hash = cursor.fetchone()

            if encrypted:
                encrypted_string = (password)
                if is_hash(password):
                    if current_pass_hash[0] != encrypted_string:
                        if module.check_mode:
                            return True
                        if not use_user_for_non_priv:
                            cursor.execute("SET PASSWORD FOR %s@%s = %s", (user, host, password))
                        else:
                            cursor.execute("ALTER USER %s@%s IDENTIFIED WITH mysql_native_password AS %s",
                                           (user, host, password))
                        changed = True
                else:
                    module.fail_json(
                        msg="encrypted was specified however it does not appear to be a valid hash expecting: *SHA1(SHA1(your_password))")
            else:
                if not use_user_for_non_priv:
                    cursor.execute("SELECT PASSWORD(%s)", (password,))
                else:
                    cursor.execute("SELECT CONCAT('*', UCASE(SHA1(UNHEX(SHA1(%s)))))", (password,))
                new_pass_hash = cursor.fetchone()
                if current_pass_hash[0] != new_pass_hash[0]:
                    if module.check_mode:
                        return True
                    if not use_user_for_non_priv:
                        cursor.execute("SET PASSWORD FOR %s@%s = PASSWORD(%s)", (user, host, password))
                    else:
                        cursor.execute("ALTER USER %s@%s IDENTIFIED WITH mysql_native_password BY %s",
                                       (user, host, password))
                    changed = True

        # Handle SSL
        if new_require_ssl:
            curr_require_ssl = user_has_require_ssl(cursor, user, host)
            if not curr_require_ssl:
                if module.check_mode:
                    return True
                user_set_require_ssl(cursor, user, host, use_user_for_non_priv)
                changed = True

        # Handle privileges
        if new_priv is not None:
            curr_priv = privileges_get(cursor, user, host)

            # If the user has privileges on a db.table that doesn't appear at all in
            # the new specification, then revoke all privileges on it.
            for db_table, priv in iteritems(curr_priv):
                # If the user has the GRANT OPTION on a db.table, revoke it first.
                if "GRANT" in priv:
                    grant_option = True
                if db_table not in new_priv:
                    if user != "root" and "PROXY" not in priv and not append_privs:
                        if module.check_mode:
                            return True
                        privileges_revoke(cursor, user, host, db_table, priv, grant_option)
                        changed = True

            # If the user doesn't currently have any privileges on a db.table, then
            # we can perform a straight grant operation.
            for db_table, priv in iteritems(new_priv):
                if db_table not in curr_priv:
                    if module.check_mode:
                        return True
                    privileges_grant(cursor, user, host, db_table, priv)
                    changed = True

            # If the db.table specification exists in both the user's current privileges
            # and in the new privileges, then we need to see if there's a difference.
            db_table_intersect = set(new_priv.keys()) & set(curr_priv.keys())
            for db_table in db_table_intersect:
                priv_diff = set(new_priv[db_table]) ^ set(curr_priv[db_table])
                if len(priv_diff) > 0:
                    if module.check_mode:
                        return True
                    if not append_privs:
                        privileges_revoke(cursor, user, host, db_table, curr_priv[db_table], grant_option)
                    privileges_grant(cursor, user, host, db_table, new_priv[db_table])
                    changed = True

    return changed


def user_delete(cursor, user, host, host_all, check_mode):
    if check_mode:
        return True

    if host_all:
        hostnames = user_get_hostnames(cursor, [user])

        for hostname in hostnames:
            cursor.execute("DROP USER %s@%s", (user, hostname))
    else:
        cursor.execute("DROP USER %s@%s", (user, host))

    return True


def user_get_hostnames(cursor, user):
    cursor.execute("SELECT Host FROM mysql.user WHERE user = %s", user)
    hostnames_raw = cursor.fetchall()
    hostnames = []

    for hostname_raw in hostnames_raw:
        hostnames.append(hostname_raw[0])

    return hostnames


def privileges_get(cursor, user, host):
    """ MySQL doesn't have a better method of getting privileges aside from the
    SHOW GRANTS query syntax, which requires us to then parse the returned string.
    Here's an example of the string that is returned from MySQL:

     GRANT USAGE ON *.* TO 'user'@'localhost' IDENTIFIED BY 'pass';

    This function makes the query and returns a dictionary containing the results.
    The dictionary format is the same as that returned by privileges_unpack() below.
    """
    output = {}
    cursor.execute("SHOW GRANTS FOR %s@%s", (user, host))
    grants = cursor.fetchall()

    def pick(x):
        if x == 'ALL PRIVILEGES':
            return 'ALL'
        else:
            return x

    for grant in grants:
        res = re.match("""GRANT (.+) ON (.+) TO (['`"]).*\\3@(['`"]).*\\4( IDENTIFIED BY PASSWORD (['`"]).+\5)? ?(.*)""", grant[0])
        if res is None:
            raise InvalidPrivsError('unable to parse the MySQL grant string: %s' % grant[0])
        privileges = res.group(1).split(", ")
        privileges = [pick(x) for x in privileges]
        if "WITH GRANT OPTION" in res.group(7):
            privileges.append('GRANT')
        db = res.group(2)
        output[db] = privileges
    return output


def privileges_unpack(priv, mode):
    """ Take a privileges string, typically passed as a parameter, and unserialize
    it into a dictionary, the same format as privileges_get() above. We have this
    custom format to avoid using YAML/JSON strings inside YAML playbooks. Example
    of a privileges string:

     mydb.*:INSERT,UPDATE/anotherdb.*:SELECT/yetanother.*:ALL

    The privilege USAGE stands for no privileges, so we add that in on *.* if it's
    not specified in the string, as MySQL will always provide this by default.
    """
    if mode == 'ANSI':
        quote = '"'
    else:
        quote = '`'
    output = {}
    privs = []
    for item in priv.strip().split('/'):
        pieces = item.strip().rsplit(':', 1)
        dbpriv = pieces[0].rsplit(".", 1)

        # Check for FUNCTION or PROCEDURE object types
        parts = dbpriv[0].split(" ", 1)
        object_type = ''
        if len(parts) > 1 and (parts[0] == 'FUNCTION' or parts[0] == 'PROCEDURE'):
            object_type = parts[0] + ' '
            dbpriv[0] = parts[1]

        # Do not escape if privilege is for database or table, i.e.
        # neither quote *. nor .*
        for i, side in enumerate(dbpriv):
            if side.strip('`') != '*':
                dbpriv[i] = '%s%s%s' % (quote, side.strip('`'), quote)
        pieces[0] = object_type + '.'.join(dbpriv)

        if '(' in pieces[1]:
            output[pieces[0]] = re.split(r',\s*(?=[^)]*(?:\(|$))', pieces[1].upper())
            for i in output[pieces[0]]:
                privs.append(re.sub(r'\s*\(.*\)', '', i))
        else:
            output[pieces[0]] = pieces[1].upper().split(',')
            privs = output[pieces[0]]
        new_privs = frozenset(privs)
        if not new_privs.issubset(VALID_PRIVS):
            raise InvalidPrivsError('Invalid privileges specified: %s' % new_privs.difference(VALID_PRIVS))

    if '*.*' not in output:
        output['*.*'] = ['USAGE']

    return output


def privileges_revoke(cursor, user, host, db_table, priv, grant_option):
    # Escape '%' since mysql db.execute() uses a format string
    db_table = db_table.replace('%', '%%')
    if grant_option:
        query = ["REVOKE GRANT OPTION ON %s" % db_table]
        query.append("FROM %s@%s")
        query = ' '.join(query)
        cursor.execute(query, (user, host))
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["REVOKE %s ON %s" % (priv_string, db_table)]
    query.append("FROM %s@%s")
    query = ' '.join(query)
    cursor.execute(query, (user, host))


def privileges_grant(cursor, user, host, db_table, priv):
    # Escape '%' since mysql db.execute uses a format string and the
    # specification of db and table often use a % (SQL wildcard)
    db_table = db_table.replace('%', '%%')
    priv_string = ",".join([p for p in priv if p not in ('GRANT', 'REQUIRESSL')])
    query = ["GRANT %s ON %s" % (priv_string, db_table)]
    query.append("TO %s@%s")
    if 'GRANT' in priv:
        query.append("WITH GRANT OPTION")
    query = ' '.join(query)
    cursor.execute(query, (user, host))


def user_has_require_ssl(cursor, user, host):
    cursor.execute("SELECT ssl_type FROM user WHERE User=%s AND Host=%s", (user, host))
    result = cursor.fetchone()
    ssl_type = result[0]

    return ssl_type.lower() == 'any'


def user_set_require_ssl(cursor, user, host, use_user_for_non_priv):
    if use_user_for_non_priv:
        query = 'ALTER USER %s@%s REQUIRE SSL'
    else:
        query = 'GRANT USAGE ON *.* TO %s@%s REQUIRE SSL'

    cursor.execute(query, (user, host))


# ===========================================
# Module execution.
#
def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_user=dict(default=None),
            login_password=dict(default=None, no_log=True),
            login_host=dict(default="localhost"),
            login_port=dict(default=3306, type='int'),
            login_unix_socket=dict(default=None),
            user=dict(required=True, aliases=['name']),
            password=dict(default=None, no_log=True, type='str'),
            require_ssl=dict(default=False, type='bool'),
            encrypted=dict(default=False, type='bool'),
            host=dict(default="localhost"),
            host_all=dict(type="bool", default="no"),
            state=dict(default="present", choices=["absent", "present"]),
            priv=dict(default=None),
            append_privs=dict(default=False, type='bool'),
            check_implicit_admin=dict(default=False, type='bool'),
            update_password=dict(default="always", choices=["always", "on_create"]),
            connect_timeout=dict(default=30, type='int'),
            config_file=dict(default="~/.my.cnf", type='path'),
            sql_log_bin=dict(default=True, type='bool'),
            ssl_cert=dict(default=None, type='path'),
            ssl_key=dict(default=None, type='path'),
            ssl_ca=dict(default=None, type='path'),
        ),
        supports_check_mode=True,
    )
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    user = module.params["user"]
    password = module.params["password"]
    require_ssl = module.params["require_ssl"]
    encrypted = module.boolean(module.params["encrypted"])
    host = module.params["host"].lower()
    host_all = module.params["host_all"]
    state = module.params["state"]
    priv = module.params["priv"]
    check_implicit_admin = module.params['check_implicit_admin']
    connect_timeout = module.params['connect_timeout']
    config_file = module.params['config_file']
    append_privs = module.boolean(module.params["append_privs"])
    update_password = module.params['update_password']
    ssl_cert = module.params["ssl_cert"]
    ssl_key = module.params["ssl_key"]
    ssl_ca = module.params["ssl_ca"]
    db = 'mysql'
    sql_log_bin = module.params["sql_log_bin"]

    if mysql_driver is None:
        module.fail_json(msg=mysql_driver_fail_msg)

    cursor = None
    try:
        if check_implicit_admin:
            try:
                cursor = mysql_connect(module, 'root', '', config_file, ssl_cert, ssl_key, ssl_ca, db,
                                       connect_timeout=connect_timeout)
            except Exception:
                pass

        if not cursor:
            cursor = mysql_connect(module, login_user, login_password, config_file, ssl_cert, ssl_key, ssl_ca, db,
                                   connect_timeout=connect_timeout)
    except Exception as e:
        module.fail_json(
            msg="unable to connect to database, check login_user and login_password are correct or %s has the credentials. "
                "Exception message: %s" % (config_file, to_native(e)))

    if not sql_log_bin:
        cursor.execute("SET SQL_LOG_BIN=0;")

    if priv is not None:
        try:
            mode = get_mode(cursor)
        except Exception as e:
            module.fail_json(msg=to_native(e))
        try:
            priv = privileges_unpack(priv, mode)
        except Exception as e:
            module.fail_json(msg="invalid privileges string: %s" % to_native(e))

        # fallback for old style REQUIRE SSL.
        if 'REQUIRESSL' in priv['*.*']:
            module.deprecate('special privilege REQUIRESSL is now a normal option', '2.5.0')
            priv['*.*'].remove('REQUIRESSL')  # remove to not use any longer
            require_ssl = True

    if state == "present":
        if user_exists(cursor, user, host, host_all):
            try:
                if update_password == 'always':
                    changed = user_mod(cursor, user, host, host_all, password, encrypted, priv, require_ssl,
                                       append_privs, module)
                else:
                    changed = user_mod(cursor, user, host, host_all, None, encrypted, priv, require_ssl, append_privs,
                                       module)

            except (SQLParseError, InvalidPrivsError, mysql_driver.Error) as e:
                module.fail_json(msg=to_native(e))
        else:
            if host_all:
                module.fail_json(msg="host_all parameter cannot be used when adding a user")
            try:
                changed = user_add(cursor, user, host, host_all, password, encrypted, priv, require_ssl,
                                   module.check_mode)
            except (SQLParseError, InvalidPrivsError, MySQLdb.Error) as e:
                module.fail_json(msg=to_native(e), exception=traceback.format_exc())
    elif state == "absent":
        if user_exists(cursor, user, host, host_all):
            changed = user_delete(cursor, user, host, host_all, module.check_mode)
        else:
            changed = False
    module.exit_json(changed=changed, user=user)


if __name__ == '__main__':
    main()
