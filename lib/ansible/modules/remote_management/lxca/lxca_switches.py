#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
version_added: "2.8"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_switches
short_description: Custom module for lxca switches inventory utility
description:
  - This module returns/displays a inventory details of switches and enable/disable ports

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter switches information
    default: switches
    choices:
      - switches
      - switches_by_uuid
      - switches_by_chassis_uuid
      - switches_list_ports
      - switches_change_status_of_ports

  chassis:
    description:
      uuid of chassis, this is string with length greater than 16.

  ports:
    description:
      ports of switch to operate on its comma separated string.

  ports_action:
    description:
      enable or disable ports of switch.
    choices:
      - None
      - enable
      - disable

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all switches info
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific switches info by uuid
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_by_uuid

# get specific switches info by chassis uuid
- name: get switches data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_by_chassis_uuid

# get particular switch ports
- name: get particular switch ports detailed data from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: switches_list_ports

# Update switch ports
# ports = [1,3]
- name: Update switch ports from LXCA
  lxca_switches:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    ports_action: enabled
    ports: "{{ports}}"
    command_options: switches_change_status_of_ports

'''

RETURN = r'''
result:
    description: switches detail from lxca
    returned: success
    type: dict
    sample:
      switchList:
        - machineType: ''
          model: ''
          type: 'Switch'
          uuid: '118D2C88C8FD11E4947B6EAE8B4BDCDF'
          # bunch of properties
        - machineType: ''
          model: ''
          type: 'Switch'
          uuid: '223D2C88C8FD11E4947B6EAE8B4BDCDF'
          # bunch of properties
        # Multiple switches details
'''

import traceback
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.remote_management.lxca.common import LXCA_COMMON_ARGS, has_pylxca, connection_object
try:
    from pylxca import switches
except ImportError:
    pass


UUID_REQUIRED = 'UUID of device is required for switches_by_uuid command.'
UUID_REQUIRED_FOR_LIST_PORTS = 'UUID of device is required for switches_list_ports command.'
UUID_REQUIRED_FOR_PORTS_ACTION = 'UUID of device is required for switches_change_status_of_ports command.'
CHASSIS_UUID_REQUIRED = 'UUID of chassis is required for switches_by_chassis_uuid command.'
PORTS_ACTION_REQUIRED = 'ports_action is required for switches_change_status_of_ports command.'
PORTS_REQUIRED = 'ports is required for switches_change_status_of_ports command.'
SUCCESS_MSG = "Success %s result"
__changed__ = False


def _switches(module, lxca_con):
    return switches(lxca_con)


def _switches_by_uuid(module, lxca_con):
    if not module.params['uuid']:
        module.fail_json(msg=UUID_REQUIRED)
    return switches(lxca_con, uuid=module.params['uuid'])


def _switches_by_chassis_uuid(module, lxca_con):
    if not module.params['chassis']:
        module.fail_json(msg=CHASSIS_UUID_REQUIRED)
    return switches(lxca_con, chassis=module.params['chassis'])


def switches_list_ports(module, lxca_con):
    if not module.params['uuid']:
        module.fail_json(msg=UUID_REQUIRED_FOR_LIST_PORTS)

    return switches(lxca_con, uuid=module.params['uuid'], ports="")


def switches_change_status_of_ports(module, lxca_con):
    global __changed__
    if not module.params['uuid']:
        module.fail_json(msg=UUID_REQUIRED_FOR_PORTS_ACTION)
    if not module.params['ports_action']:
        module.fail_json(msg=PORTS_ACTION_REQUIRED)
    if not module.params['ports']:
        module.fail_json(msg=PORTS_REQUIRED)

    __changed__ = True
    return switches(lxca_con, uuid=module.params['uuid'],
                    ports=module.params['ports'],
                    action=module.params['ports_action'])


def setup_module_object():
    """
    this function merge argument spec and create ansible module object
    :return:
    """
    args_spec = dict(LXCA_COMMON_ARGS)
    args_spec.update(INPUT_ARG_SPEC)
    module = AnsibleModule(argument_spec=args_spec, supports_check_mode=False)

    return module


FUNC_DICT = {
    'switches': _switches,
    'switches_by_uuid': _switches_by_uuid,
    'switches_by_chassis_uuid': _switches_by_chassis_uuid,
    'switches_list_ports': switches_list_ports,
    'switches_change_status_of_ports': switches_change_status_of_ports,
}


INPUT_ARG_SPEC = dict(
    command_options=dict(default='switches', choices=['switches',
                                                      'switches_by_uuid',
                                                      'switches_by_chassis_uuid',
                                                      'switches_list_ports',
                                                      'switches_change_status_of_ports']),
    uuid=dict(default=None),
    chassis=dict(default=None),
    ports=dict(default=None),
    ports_action=dict(default=None, choices=[None, 'enable', 'disable'])
)


def execute_module(module):
    """
    This function invoke commands
    :param module: Ansible module object
    """
    try:
        with connection_object(module) as lxca_con:
            result = FUNC_DICT[module.params['command_options']](module, lxca_con)
            module.exit_json(changed=__changed__,
                             msg=SUCCESS_MSG % module.params['command_options'],
                             result=result)
    except Exception as exception:
        error_msg = '; '.join((e) for e in exception.args)
        module.fail_json(msg=error_msg, exception=traceback.format_exc())


def main():
    module = setup_module_object()
    has_pylxca(module)
    execute_module(module)


if __name__ == '__main__':
    main()
