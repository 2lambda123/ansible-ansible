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
module: checkpoint_publish
short_description: publish session on Checkpoint devices over Web Services API
description:
  - Publish session on Checkpoint devices.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  uid:
    description:
      - Session unique identifier. Specify it to publish a different session than the one you currently use.
    type: str
extends_documentation_fragment: checkpoint_commands
"""

EXAMPLES = """
- name: publish
  checkpoint_publish:
"""

RETURN = """
checkpoint_publish:
  description: The checkpoint publish output.
  returned: always.
  type: str
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_commands, api_command


def main():
    argument_spec = dict(
        uid=dict(type='str'),
        wait_for_task=dict(type='bool', default=True)
    )
    argument_spec.update(checkpoint_argument_spec_for_commands)

    module = AnsibleModule(argument_spec=argument_spec)

    command = "publish"

    api_command(module, command)


if __name__ == '__main__':
    main()
