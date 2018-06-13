#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2018 Dell EMC Inc.
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: redfish
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    get information back or perform an action.
  - When receiving information, it is placed in location specified by user.
options:
  category:
    required: true
    description:
      - Action category to execute on server
    choices: ["Inventory", "Accounts", "System", "Update", "Manager", "Chassis"]
  command:
    required: true
    description:
      - Command to execute on server
  baseuri:
    required: true
    description:
      - Base URI of OOB controller
  user:
    required: true
    description:
      - User for authentication with OOB controller
  password:
    required: true
    description:
      - Password for authentication with OOB controller
  userid:
    required: false
    description:
      - ID of user to add/delete/modify
  username:
    required: false
    description:
      - name of user to add/delete/modify
  userpswd:
    required: false
    description:
      - password of user to add/delete/modify
  userrole:
    required: false
    description:
      - role of user to add/delete/modify
  bootdevice:
    required: false
    description:
      - bootdevice when setting boot configuration
  bios_attr_name:
    required: false
    description:
      - name of BIOS attribute to update
  bios_attr_value:
    required: false
    description:
      - value of BIOS attribute to update to
  mgr_attr_name:
    required: false
    description:
      - name of Manager attribute to update
  mgr_attr_value:
    required: false
    description:
      - value of Manager attribute to update to

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Getting system inventory
    redfish:
      category: Inventory
      command: GetSystemInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Get CPU Inventory
    redfish:
      category: Inventory
      command: GetCpuInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user}}"
      password: "{{ password }}"

  - name: Enable PXE Boot for NIC1
    redfish:
      category: System
      command: SetBiosAttributes
      bios_attr_name: PxeDev1EnDis
      bios_attr_value: Enabled
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Set one-time boot device to {{ bootdevice }}
    redfish:
      category: System
      command: SetOneTimeBoot
      bootdevice: "{{ bootdevice }}"
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Turn system power on
    redfish:
      category: System
      command: PowerOn
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Add user
    redfish:
      category: Accounts
      command: AddUser
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
      userid: "{{ userid }}"
      username: "{{ username }}"
      userpswd: "{{ userpswd }}"
      userrole: "{{ userrole }}"

  - name: Enable user
    redfish:
      category: Accounts
      command: EnableUser
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
      userid: "{{ userid }}"

  - name: Get attributes
    redfish:
      category: System
      command: GetBiosAttributes
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
'''

RETURN = '''
result:
    description: different results depending on task
    returned: always
    type: dict
    sample: BIOS Attributes set as pending values
'''

import os
import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils


def main():
    result = {}
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True, choices=["Inventory", "Accounts", "System", "Update", "Manager", "Chassis"]),
            command=dict(required=True),
            baseuri=dict(required=True),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
            userid=dict(),
            username=dict(),
            userpswd=dict(no_log=True),
            userrole=dict(),
            bootdevice=dict(),
            mgr_attr_name=dict(),
            mgr_attr_value=dict(),
            bios_attr_name=dict(),
            bios_attr_value=dict(),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command = module.params['command']
    bootdevice = module.params['bootdevice']

    # admin credentials used for authentication
    creds = {'user': module.params['user'],
             'pswd': module.params['password']}

    # user to add/modify/delete
    user = {'userid': module.params['userid'],
            'username': module.params['username'],
            'userpswd': module.params['userpswd'],
            'userrole': module.params['userrole']}

    # Manager attributes to update
    mgr_attributes = {'mgr_attr_name': module.params['mgr_attr_name'],
                      'mgr_attr_value': module.params['mgr_attr_value']}
    # BIOS attributes to update
    bios_attributes = {'bios_attr_name': module.params['bios_attr_name'],
                       'bios_attr_value': module.params['bios_attr_value']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1"
    rf_utils = RedfishUtils(creds, root_uri)

    # Organize by Categories / Commands
    if category == "Inventory":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        # General
        if command == "GetSystemInventory":
            result = rf_utils.get_system_inventory()

        # Components
        elif command == "GetPsuInventory":
            result = rf_utils.get_psu_inventory()
        elif command == "GetCpuInventory":
            result = rf_utils.get_cpu_inventory()
        elif command == "GetNicInventory":
            result = rf_utils.get_nic_inventory()

        # Storage
        elif command == "GetStorageControllerInventory":
            result = rf_utils.get_storage_controller_inventory()
        elif command == "GetDiskInventory":
            result = rf_utils.get_disk_inventory()

        # Chassis
        elif command == "GetFanInventory":
            # execute only if we find Chassis resource
            result = rf_utils._find_chassis_resource(rf_uri)
            if result['ret'] is False:
                module.fail_json(msg=result['msg'])
            result = rf_utils.get_fan_inventory()

        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Accounts":
        # execute only if we find an Account service resource
        result = rf_utils._find_accountservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "ListUsers":
            result = rf_utils.list_users(user)
        elif command == "AddUser":
            result = rf_utils.add_user(user)
        elif command == "EnableUser":
            result = rf_utils.enable_user(user)
        elif command == "DeleteUser":
            result = rf_utils.delete_user(user)
        elif command == "DisableUser":
            result = rf_utils.disable_user(user)
        elif command == "UpdateUserRole":
            result = rf_utils.update_user_role(user)
        elif command == "UpdateUserPassword":
            result = rf_utils.update_user_password(user)
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "System":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "PowerOn" or command == "PowerForceOff" \
                or command == "PowerGracefulRestart" \
                or command == "PowerGracefulShutdown":
            result = rf_utils.manage_system_power(command)
        elif command == "GetBiosAttributes":
            result = rf_utils.get_bios_attributes()
        elif command == "GetBiosBootOrder":
            result = rf_utils.get_bios_boot_order()
        elif command == "SetOneTimeBoot":
            result = rf_utils.set_one_time_boot_device(bootdevice)
        elif command == "SetBiosDefaultSettings":
            result = rf_utils.set_bios_default_settings()
        elif command == "SetBiosAttributes":
            result = rf_utils.set_bios_attributes(bios_attributes)
        elif command == "CreateBiosConfigJob":
            # execute only if we find a Managers resource
            result = rf_utils._find_managers_resource(rf_uri)
            if result['ret'] is False:
                module.fail_json(msg=result['msg'])
            result = rf_utils.create_bios_config_job()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Update":
        # execute only if we find UpdateService resources
        result = rf_utils._find_updateservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "GetFirmwareInventory":
            result = rf_utils.get_firmware_inventory()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        if command == "GracefulRestart":
            result = rf_utils.restart_manager_gracefully()
        elif command == "GetAttributes":
            result = rf_utils.get_manager_attributes()
        elif command == "SetAttributes":
            result = rf_utils.set_manager_attributes(mgr_attributes)

        # Logs
        elif command == "GetLogs":
            result = rf_utils.get_logs()
        elif command == "ClearLogs":
            result = rf_utils.clear_logs()
        else:
            result = {'ret': False, 'msg': 'Invalid Command'}

    else:
        result = {'ret': False, 'msg': 'Invalid Category'}

    # Return data back or fail with proper message
    if result['ret'] is True:
        del result['ret']
        module.exit_json(result=result)
    else:
        module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()
