#!/usr/bin/python
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: checkpoint_address_range
short_description: Manages address_range objects on Checkpoint over Web Services API
description:
  - Manages address_range objects on Checkpoint devices including creating, updating, removing address_range objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  ip_address_first:
    description:
      - First IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and
        the ipv6-address-first fields instead.
    type: str
  ipv4_address_first:
    description:
      - First IPv4 address in the range.
    type: str
  ipv6_address_first:
    description:
      - First IPv6 address in the range.
    type: str
  ip_address_last:
    description:
      - Last IP address in the range. If both IPv4 and IPv6 address ranges are required, use the ipv4-address-first and
        the ipv6-address-first fields instead.
    type: str
  ipv4_address_last:
    description:
      - Last IPv4 address in the range.
    type: str
  ipv6_address_last:
    description:
      - Last IPv6 address in the range.
    type: str
  nat_settings:
    description:
      - NAT settings.
    type: dict
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: Add address_range object
  checkpoint_address_range:
    name: "New address_range 1"
    ip-address-first: "192.0.2.1"
    ip-address-last: "192.0.2.10"
    state: present


- name: Delete address_range object
  checkpoint_address_range:
    name: "New Address Range 1"
    state: absent
"""

RETURN = """
checkpoint_address_ranges:
  description: The checkpoint address_range object created or updated.
  returned: always, except when deleting the address_range.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec, api_call


def main():
    argument_spec = dict(
        ip_address_first=dict(type='str'),
        ipv4_address_first=dict(type='str'),
        ipv6_address_first=dict(type='str'),
        ip_address_last=dict(type='int'),
        ipv4_address_last=dict(type='int'),
        ipv6_address_last=dict(type='int'),
        nat_settings=dict(type='dict')
    )
    argument_spec.update(checkpoint_argument_spec)
    user_parameters = list(argument_spec.keys())
    user_parameters.remove('auto_publish_session')
    user_parameters.remove('state')

    module = AnsibleModule(argument_spec=argument_spec, required_one_of=[['name', 'uid']],
                           mutually_exclusive=[['name', 'uid']])
    api_call_object = "network"

    unique_payload_for_get = {'name': module.params['name']} if module.params['name'] else {'uid': module.params['uid']}

    api_call(module, api_call_object, user_parameters, unique_payload_for_get)


if __name__ == '__main__':
    main()
