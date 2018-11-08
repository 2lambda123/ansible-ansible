#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (c) 2018, Ingate Systems AB
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

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: ig_store_edit
short_description: Store the preliminary configuration on an Ingate SBC.
description:
  - Store the preliminary configuration to the permanent configuration on an
    Ingate SBC.
version_added: 2.8
extends_documentation_fragment: ingate
options:
  no_response:
    description:
      - Toggels if a response is excpected.
    type: bool
    default: false
notes:
  - The no_response argument must be set to True if you have changed the IP
    address on the interface that you are currently connecting to.
author:
  - Ingate Systems AB (@ingatesystems)
'''

EXAMPLES = '''
- name: Store the preliminary configuration
  ig_store_edit:
    client:
      version: v1
      scheme: http
      address: 192.168.1.1
      username: alice
      password: foobar
'''

RETURN = '''
store-edit:
  description: A command status message
  returned: success
  type: complex
  contains:
    msg:
      description: The command status message
      returned: success
      type: string
      sample: Successfully applied and saved the configuration.
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.ingate.common import (ingate_argument_spec,
                                                        ingate_create_client)

try:
    from ingate import ingatesdk
    HAS_INGATESDK = True
except ImportError:
    HAS_INGATESDK = False


def make_request(module):
    # Create client and authenticate.
    api_client = ingate_create_client(**module.params)

    # Store the preliminary configuration.
    no_response = module.params.get('no_response')
    response = api_client.store_edit(no_response=no_response)
    return response


def main():
    argument_spec = ingate_argument_spec(
        no_response=dict(default=False, type=bool),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=False)
    if not HAS_INGATESDK:
        module.fail_json(msg='The Ingate Python SDK module is required')

    result = dict(changed=False)
    try:
        response = make_request(module)
        if response:
            result.update(response[0])
        result['changed'] = True
    except ingatesdk.SdkError as e:
        module.fail_json(msg=str(e))
    module.exit_json(**result)


if __name__ == '__main__':
    main()
