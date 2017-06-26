#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, Chatham Financial <oss@chathamfinancial.com>
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

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_global_parameter
short_description: Adds or removes global parameters to RabbitMQ
description:
  - Manage dynamic, cluster-wide global parameters for RabbitMQ
version_added: "2.3"
author: '"Juergen Kirschbaum (@gmail.com)"'
options:
  name:
    description:
      - Name of the global parameter being set
    required: true
    default: null
  value:
    description:
      - Value of the global parameter, as a JSON term
    required: false
    default: null
  node:
    description:
      - erlang node name of the rabbit we wish to configure
    required: false
    default: rabbit
  state:
    description:
      - Specify if user is to be added or removed
    required: false
    default: present
    choices: [ 'present', 'absent']
'''

EXAMPLES = """
# Set the global parameter 'cluster_name' to a value of 'mq-cluster' (in quotes)
- rabbitmq_global_parameter: name=cluster_name
                             value='"mq-cluster"'
                             state=present
"""

from ansible.module_utils.basic import AnsibleModule, json


class RabbitMqParameter(object):
    def __init__(self, module, name, value, node):
        self.module = module
        self.name = name
        self.value = value
        self.node = node

        self._value = None

        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self.module.check_mode or (self.module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self.node]
            rc, out, err = self.module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get(self):
        global_parameters = self._exec(['list_global_parameters'], True)

        for param_item in global_parameters:
            name, value = param_item.split('\t')

            if name == self.name:
                self._value = json.loads(value)
                return True
        return False

    def set(self):
        self._exec(['set_global_parameter',
                    self.name,
                    json.dumps(self.value)])

    def delete(self):
        self._exec(['clear_global_parameter', self.name])

    def has_modifications(self):
        return self.value != self._value


def main():
    arg_spec = dict(
        name=dict(required=True),
        value=dict(default=None),
        state=dict(default='present', choices=['present', 'absent']),
        node=dict(default='rabbit')
    )
    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    name = module.params['name']
    value = module.params['value']
    if isinstance(value, str):
        value = json.loads(value)
    state = module.params['state']
    node = module.params['node']

    rabbitmq_global_parameter = RabbitMqParameter(module, name, value, node)

    changed = False
    if rabbitmq_global_parameter.get():
        if state == 'absent':
            rabbitmq_global_parameter.delete()
            changed = True
        else:
            if rabbitmq_global_parameter.has_modifications():
                rabbitmq_global_parameter.set()
                changed = True
    elif state == 'present':
        rabbitmq_global_parameter.set()
        changed = True

    module.exit_json(changed=changed, name=name, state=state)

main()
