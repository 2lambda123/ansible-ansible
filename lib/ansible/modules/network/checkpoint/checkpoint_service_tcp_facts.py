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
module: checkpoint_service_tcp_facts
short_description: Get service_tcp objects facts on Checkpoint over Web Services API
description:
  - Get service_tcp objects facts on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
extends_documentation_fragment: checkpoint_facts
"""

EXAMPLES = """
- name: Get service_tcp object facts
  checkpoint_service_tcp_facts:
    name: "New_TCP_Service_1"
"""

RETURN = """
api_result:
  description: The checkpoint object facts.
  returned: always.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_facts, api_call_facts


def main():
    argument_spec = dict()
    argument_spec.update(checkpoint_argument_spec_for_facts)
    user_parameters = list(argument_spec.keys())

    module = AnsibleModule(argument_spec=argument_spec)
    api_call_object = "service_tcp"

    api_call_facts(module, api_call_object, user_parameters)


if __name__ == '__main__':
    main()
