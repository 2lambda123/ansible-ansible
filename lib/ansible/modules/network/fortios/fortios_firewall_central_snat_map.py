#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
# Copyright 2019 Fortinet, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# the lib use python logging can get it if the following is set in your
# Ansible config.

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: fortios_firewall_central_snat_map
short_description: Configure central SNAT policies in Fortinet's FortiOS and FortiGate.
description:
    - This module is able to configure a FortiGate or FortiOS by
      allowing the user to configure firewall feature and central_snat_map category.
      Examples includes all options and need to be adjusted to datasources before usage.
      Tested with FOS v6.0.2
version_added: "2.8"
author:
    - Miguel Angel Munoz (@mamunozgonzalez)
    - Nicolas Thomas (@thomnico)
notes:
    - Requires fortiosapi library developed by Fortinet
    - Run as a local_action in your playbook
requirements:
    - fortiosapi>=0.9.8
options:
    host:
       description:
            - FortiOS or FortiGate ip address.
       required: true
    username:
        description:
            - FortiOS or FortiGate username.
        required: true
    password:
        description:
            - FortiOS or FortiGate password.
        default: ""
    vdom:
        description:
            - Virtual domain, among those defined previously. A vdom is a
              virtual instance of the FortiGate that can be configured and
              used as a different unit.
        default: root
    https:
        description:
            - Indicates if the requests towards FortiGate must use HTTPS
              protocol
        type: bool
        default: false
    firewall_central_snat_map:
        description:
            - Configure central SNAT policies.
        default: null
        suboptions:
            state:
                description:
                    - Indicates whether to create or remove the object
                choices:
                    - present
                    - absent
            comments:
                description:
                    - Comment.
            dst-addr:
                description:
                    - Destination address name from available addresses.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            dstintf:
                description:
                    - Destination interface name from available interfaces.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            nat:
                description:
                    - Enable/disable source NAT.
                choices:
                    - disable
                    - enable
            nat-ippool:
                description:
                    - Name of the IP pools to be used to translate addresses from available IP Pools.
                suboptions:
                    name:
                        description:
                            - IP pool name. Source firewall.ippool.name.
                        required: true
            nat-port:
                description:
                    - Translated port or port range (0 to 65535).
            orig-addr:
                description:
                    - Original address.
                suboptions:
                    name:
                        description:
                            - Address name. Source firewall.address.name firewall.addrgrp.name.
                        required: true
            orig-port:
                description:
                    - Original TCP port (0 to 65535).
            policyid:
                description:
                    - Policy ID.
                required: true
            protocol:
                description:
                    - Integer value for the protocol type (0 - 255).
            srcintf:
                description:
                    - Source interface name from available interfaces.
                suboptions:
                    name:
                        description:
                            - Interface name. Source system.interface.name system.zone.name.
                        required: true
            status:
                description:
                    - Enable/disable the active status of this policy.
                choices:
                    - enable
                    - disable
'''

EXAMPLES = '''
- hosts: localhost
  vars:
   host: "192.168.122.40"
   username: "admin"
   password: ""
   vdom: "root"
  tasks:
  - name: Configure central SNAT policies.
    fortios_firewall_central_snat_map:
      host:  "{{ host }}"
      username: "{{ username }}"
      password: "{{ password }}"
      vdom:  "{{ vdom }}"
      firewall_central_snat_map:
        state: "present"
        comments: "<your_own_value>"
        dst-addr:
         -
            name: "default_name_5 (source firewall.address.name firewall.addrgrp.name)"
        dstintf:
         -
            name: "default_name_7 (source system.interface.name system.zone.name)"
        nat: "disable"
        nat-ippool:
         -
            name: "default_name_10 (source firewall.ippool.name)"
        nat-port: "<your_own_value>"
        orig-addr:
         -
            name: "default_name_13 (source firewall.address.name firewall.addrgrp.name)"
        orig-port: "<your_own_value>"
        policyid: "15"
        protocol: "16"
        srcintf:
         -
            name: "default_name_18 (source system.interface.name system.zone.name)"
        status: "enable"
'''

RETURN = '''
build:
  description: Build number of the fortigate image
  returned: always
  type: str
  sample: '1547'
http_method:
  description: Last method used to provision the content into FortiGate
  returned: always
  type: str
  sample: 'PUT'
http_status:
  description: Last result given by FortiGate on last operation applied
  returned: always
  type: str
  sample: "200"
mkey:
  description: Master key (id) used in the last call to FortiGate
  returned: success
  type: str
  sample: "id"
name:
  description: Name of the table used to fulfill the request
  returned: always
  type: str
  sample: "urlfilter"
path:
  description: Path of the table used to fulfill the request
  returned: always
  type: str
  sample: "webfilter"
revision:
  description: Internal revision number
  returned: always
  type: str
  sample: "17.0.2.10658"
serial:
  description: Serial number of the unit
  returned: always
  type: str
  sample: "FGVMEVYYQT3AB5352"
status:
  description: Indication of the operation's result
  returned: always
  type: str
  sample: "success"
vdom:
  description: Virtual domain used
  returned: always
  type: str
  sample: "root"
version:
  description: Version of the FortiGate
  returned: always
  type: str
  sample: "v5.6.3"

'''

from ansible.module_utils.basic import AnsibleModule

fos = None


def login(data):
    host = data['host']
    username = data['username']
    password = data['password']

    fos.debug('on')
    if 'https' in data and not data['https']:
        fos.https('off')
    else:
        fos.https('on')

    fos.login(host, username, password)


def filter_firewall_central_snat_map_data(json):
    option_list = ['comments', 'dst-addr', 'dstintf',
                   'nat', 'nat-ippool', 'nat-port',
                   'orig-addr', 'orig-port', 'policyid',
                   'protocol', 'srcintf', 'status']
    dictionary = {}

    for attribute in option_list:
        if attribute in json and json[attribute] is not None:
            dictionary[attribute] = json[attribute]

    return dictionary


def firewall_central_snat_map(data, fos):
    vdom = data['vdom']
    firewall_central_snat_map_data = data['firewall_central_snat_map']
    filtered_data = filter_firewall_central_snat_map_data(firewall_central_snat_map_data)
    if firewall_central_snat_map_data['state'] == "present":
        return fos.set('firewall',
                       'central-snat-map',
                       data=filtered_data,
                       vdom=vdom)

    elif firewall_central_snat_map_data['state'] == "absent":
        return fos.delete('firewall',
                          'central-snat-map',
                          mkey=filtered_data['policyid'],
                          vdom=vdom)


def fortios_firewall(data, fos):
    login(data)

    methodlist = ['firewall_central_snat_map']
    for method in methodlist:
        if data[method]:
            resp = eval(method)(data, fos)
            break

    fos.logout()
    return not resp['status'] == "success", resp['status'] == "success", resp


def main():
    fields = {
        "host": {"required": True, "type": "str"},
        "username": {"required": True, "type": "str"},
        "password": {"required": False, "type": "str", "no_log": True},
        "vdom": {"required": False, "type": "str", "default": "root"},
        "https": {"required": False, "type": "bool", "default": "False"},
        "firewall_central_snat_map": {
            "required": False, "type": "dict",
            "options": {
                "state": {"required": True, "type": "str",
                          "choices": ["present", "absent"]},
                "comments": {"required": False, "type": "str"},
                "dst-addr": {"required": False, "type": "list",
                             "options": {
                                 "name": {"required": True, "type": "str"}
                             }},
                "dstintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "nat": {"required": False, "type": "str",
                        "choices": ["disable", "enable"]},
                "nat-ippool": {"required": False, "type": "list",
                               "options": {
                                   "name": {"required": True, "type": "str"}
                               }},
                "nat-port": {"required": False, "type": "str"},
                "orig-addr": {"required": False, "type": "list",
                              "options": {
                                  "name": {"required": True, "type": "str"}
                              }},
                "orig-port": {"required": False, "type": "str"},
                "policyid": {"required": True, "type": "int"},
                "protocol": {"required": False, "type": "int"},
                "srcintf": {"required": False, "type": "list",
                            "options": {
                                "name": {"required": True, "type": "str"}
                            }},
                "status": {"required": False, "type": "str",
                           "choices": ["enable", "disable"]}

            }
        }
    }

    module = AnsibleModule(argument_spec=fields,
                           supports_check_mode=False)
    try:
        from fortiosapi import FortiOSAPI
    except ImportError:
        module.fail_json(msg="fortiosapi module is required")

    global fos
    fos = FortiOSAPI()

    is_error, has_changed, result = fortios_firewall(module.params, fos)

    if not is_error:
        module.exit_json(changed=has_changed, meta=result)
    else:
        module.fail_json(msg="Error in repo", meta=result)


if __name__ == '__main__':
    main()
