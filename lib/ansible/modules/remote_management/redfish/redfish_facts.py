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
module: redfish_facts
version_added: "2.7"
short_description: Manages Out-Of-Band controllers using Redfish APIs
description:
  - Builds Redfish URIs locally and sends them to remote OOB controllers to
    get information back.
  - Information retrieved is placed in a location specified by the user.
options:
  category:
    required: true
    description:
      - Action category to execute on server
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

author: "Jose Delarosa (github: jose-delarosa)"
'''

EXAMPLES = '''
  - name: Get system inventory
    redfish_facts:
      category: System
      command: GetCpuInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Get system inventory (default command)
    redfish_facts:
      category: System
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Get system inventory (more than one command)
    redfish_facts:
      category: System
      command: "GetNicInventory GetPsuInventory GetBiosAttributes"
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: Get fans statistics
    redfish_facts:
      category: Chassis
      command: GetFanInventory
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"

  - name: List all users
    redfish_facts:
      category: Accounts
      command: ListUsers
      baseuri: "{{ baseuri }}"
      user: "{{ user }}"
      password: "{{ password }}"
'''

RETURN = '''
result:
    description: different results depending on task
    returned: always
    type: dict
    sample: List of CPUs on system
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.redfish_utils import RedfishUtils

CATEGORY_COMMANDS_ALL = {
    "System": ["GetSystemInventory", "GetPsuInventory", "GetCpuInventory",
               "GetNicInventory", "GetStorageControllerInventory",
               "GetDiskInventory", "GetBiosAttributes", "GetBiosBootOrder"],
    "Chassis": ["GetFanInventory"],
    "Accounts": ["ListUsers"],
    "Update": ["GetFirmwareInventory"],
    "Manager": ["GetManagerAttributes", "GetLogs"],
}

CATEGORY_COMMANDS_DEFAULT = {
    "System": "GetSystemInventory",
    "Chassis": "GetFanInventory",
    "Accounts": "ListUsers",
    "Update": "GetFirmwareInventory",
    "Manager": "GetManagerAttributes",
}


def main():
    result_all = {}
    result = {}
    cmd_list = []
    module = AnsibleModule(
        argument_spec=dict(
            category=dict(required=True),
            command=dict(),
            baseuri=dict(required=True),
            user=dict(required=True),
            password=dict(required=True, no_log=True),
        ),
        supports_check_mode=False
    )

    category = module.params['category']
    command = module.params['command']

    # admin credentials used for authentication
    creds = {'user': module.params['user'],
             'pswd': module.params['password']}

    # Build root URI
    root_uri = "https://" + module.params['baseuri']
    rf_uri = "/redfish/v1"
    rf_utils = RedfishUtils(creds, root_uri)

    # Check for valid category and command(s)
    if category in CATEGORY_COMMANDS_ALL:
        result['ret'] = True

        # true if we don't specify a command, so use default
        if not command:
            cmd_list.append(CATEGORY_COMMANDS_DEFAULT[category])

        # true if we specify the command 'all'
        elif command == "all":
            for entry in range(len(CATEGORY_COMMANDS_ALL[category])):
                cmd_list.append(CATEGORY_COMMANDS_ALL[category][entry])

        else:
            # put all commands in a list, even if it's just one
            for cmd in command.split():
                if cmd in CATEGORY_COMMANDS_ALL[category]:
                    cmd_list.append(cmd)
                else:
                    # Fail if even one command given is invalid
                    result = {'ret': False, 'msg': 'Invalid Command'}
                    break
    else:
        result = {'ret': False, 'msg': 'Invalid Category'}

    # Check for failures
    if result['ret'] is False:
        module.fail_json(msg=result['msg'])

    # Organize by Categories / Commands
    if category == "System":
        # execute only if we find a System resource
        result = rf_utils._find_systems_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        for command in cmd_list:
            if command == "GetSystemInventory":
                result["system"] = rf_utils.get_system_inventory()
            elif command == "GetPsuInventory":
                result["psu"] = rf_utils.get_psu_inventory()
            elif command == "GetCpuInventory":
                result["cpu"] = rf_utils.get_cpu_inventory()
            elif command == "GetNicInventory":
                result["nic"] = rf_utils.get_nic_inventory()
            elif command == "GetStorageControllerInventory":
                result["storage_controller"] = rf_utils.get_storage_controller_inventory()
            elif command == "GetDiskInventory":
                result["disk"] = rf_utils.get_disk_inventory()
            elif command == "GetBiosAttributes":
                result["bios_attribute"] = rf_utils.get_bios_attributes()
            elif command == "GetBiosBootOrder":
                result["bios_boot_order"] = rf_utils.get_bios_boot_order()

    elif category == "Chassis":
        # execute only if we find Chassis resource
        result = rf_utils._find_chassis_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        for command in cmd_list:
            if command == "GetFanInventory":
                result["fan"] = rf_utils.get_fan_inventory()

    elif category == "Accounts":
        # execute only if we find an Account service resource
        result = rf_utils._find_accountservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        for command in cmd_list:
            if command == "ListUsers":
                result["user"] = rf_utils.list_users()

    elif category == "Update":
        # execute only if we find UpdateService resources
        result = rf_utils._find_updateservice_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        for command in cmd_list:
            if command == "GetFirmwareInventory":
                result["firmware"] = rf_utils.get_firmware_inventory()

    elif category == "Manager":
        # execute only if we find a Manager service resource
        result = rf_utils._find_managers_resource(rf_uri)
        if result['ret'] is False:
            module.fail_json(msg=result['msg'])

        for command in cmd_list:
            if command == "GetManagerAttributes":
                result["mgr_attr"] = rf_utils.get_manager_attributes()
            elif command == "GetLogs":
                result["log"] = rf_utils.get_logs()

    # Return data back or fail with proper message
    if result['ret'] is True:
        del result['ret']
        module.exit_json(ansible_facts=result)
    else:
        module.fail_json(msg=result['msg'])

if __name__ == '__main__':
    main()
