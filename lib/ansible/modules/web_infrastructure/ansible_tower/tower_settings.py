#!/usr/bin/python
# coding: utf-8 -*-

# (c) 2018, Nikhil Jain <nikjain@redhat.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: tower_settings
author: "Nikhil Jain (@jainnikhil30)"
version_added: "2.7"
short_description: Get, Modify Ansible Tower settings.
description:
    - Get, Modify Ansible Tower settings. See
      U(https://www.ansible.com/tower) for an overview.
options:
    name:
      description:
        - Name of setting to get/modify.
    value:
      description:
        - Value to be modified for given setting. If this parameter is not given, module will only get the value of setting.
extends_documentation_fragment: tower
'''


EXAMPLES = '''
- name: Set the value of AWX_PROOT_BASE_PATH
  tower_settings:
    name: AWX_PROOT_BASE_PATH
    value: "/tmp"
  register: testing_settings

- name: Set the value of AWX_PROOT_SHOW_PATHS
  tower_settings:
    name: "AWX_PROOT_SHOW_PATHS"
    value: "'/var/lib/awx/projects/', '/tmp'"
  register: testing_settings

- name: Set the LDAP Auth Bind Password
  tower_settings:
    name: "AUTH_LDAP_BIND_PASSWORD"
    value: "Password"
  no_log: true

- name: Get the value of AWX_PROOT_BASE_PATH
  tower_settings:
    name: AWX_PROOT_BASE_PATH
'''

from ansible.module_utils.ansible_tower import TowerModule, tower_auth_config, tower_check_mode

try:
    import tower_cli
    import tower_cli.utils.exceptions as exc

    from tower_cli.conf import settings
except ImportError:
    pass


def main():
    argument_spec = dict(
        name=dict(),
        value=dict(),
    )

    module = TowerModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    json_output = {}

    name = module.params.get('name')
    value = module.params.get('value')

    tower_auth = tower_auth_config(module)
    with settings.runtime_values(**tower_auth):
        tower_check_mode(module)
        try:
            setting = tower_cli.get_resource('setting')
            if value:
                result = setting.modify(setting=name, value=value)
                json_output['changed'] = result['changed']
            else:
                result = setting.get(pk=name)

            json_output['id'] = result['id']
            json_output['value'] = result['value']

        except (exc.ConnectionError, exc.BadRequest) as excinfo:
            module.fail_json(msg='Failed to modify the setting: {0}'.format(excinfo), changed=False)

    module.exit_json(**json_output)


if __name__ == '__main__':
    main()
