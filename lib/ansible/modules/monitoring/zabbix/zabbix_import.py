#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) mateusz@sysadmins.pl
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: zabbix_import
short_description: Import zabbix configuration from xml or json
description:
   - This module allows you to import zabbix configuration from xml or json file
version_added: "2.6"
author:
    - "(@kuczko)"
requirements:
    - "python >= 2.6"
    - zabbix-api
options:
    import_file:
        description:
            - Path to file with zabbix import
        required: true
    import_format:
        description:
            - Format of zabbix import file
        choices:
            - xml
            - json
extends_documentation_fragment:
    - zabbix
'''

EXAMPLES = '''
- name: Import zabbix hosts
  local_action:
    module: zabbix_import
    server_url: http://monitor.example.com
    login_user: username
    login_password: password
    import_file: /tmp/myfile.xml
    import_format: xml
    rules:
      hosts:
        createMissing: True
    timeout: 10
'''

from ansible.module_utils.basic import AnsibleModule

try:
    from zabbix_api import ZabbixAPI

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False


default_rules=({
    'applications':{
        'createMissing':True,
        'deleteMissing':True
    },
    'discoveryRules':{
        'createMissing':True,
        'updateExisting':True,
        'deleteMissing':True
    },
    'graphs':{
        'createMissing':True,
        'updateExisting':True,
        'deleteMissing':True
    },
    'groups':{
        'createMissing':True
    },
    'hosts':{
        'createMissing':True,
        'updateExisting':True
    },
    'images':{
        'createMissing':True,
        'updateExisting':True
    },
    'items':{
        'createMissing':True,
        'updateExisting':True,
        'deleteMissing':True
    },
    'maps':{
        'createMissing':True,
        'updateExisting':True
    },
    'screens':{
        'createMissing':True,
        'updateExisting':True
    },
    'templateLinkage':{
        'createMissing':True
    },
    'templates':{
        'createMissing':True,
        'updateExisting':True
    },
    'templateScreens':{
        'createMissing':True,
        'updateExisting':True,
        'deleteMissing':True
    },
    'triggers':{
        'createMissing':True,
        'updateExisting':True,
        'deleteMissing':True
    },
    'valueMaps':{
        'createMissing':True,
        'updateExisting':True
    }
})

class Configuration(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def import_template(self, filename,rules, import_format):
        f = open(filename,'r') 
        import_string = f.read()
        import_result = self._zapi.configuration.import_({'format': import_format, 'source' : import_string , 'rules' : rules })
        return import_result

def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            import_file=dict(type='str', required=True),
            rules=dict(type='dict', required=False),
            import_format=dict(type='str', required=False, default='xml'),
            timeout=dict(type='int', default=10)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing requried zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    import_file = module.params['import_file']
    import_format = module.params['import_format']
    timeout = module.params['timeout']
    rules = module.params['rules']

    zbx = None
    # login to zabbix
    try:
        zbx = ZabbixAPI(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                               validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    # Validate format 
    if import_format.lower() not in ['xml','json']:
        self._module.fail_json(msg="import_format value incorrect: %s" % import_format)

    if rules is None:
       rules={}

    # Set default values for all empty rules
    for rule_group in default_rules:
        try:
            rules[rule_group]
        except KeyError:
            rules[rule_group]={}
        for rule in default_rules[rule_group]:
            try:
                rules[rule_group][rule]
            except KeyError:
                rules[rule_group][rule]=default_rules[rule_group][rule]
    conf = Configuration(module, zbx)
    import_task = conf.import_template(import_file,rules,import_format)

    module.exit_json(import_task=import_task)

if __name__ == '__main__':
    main()
