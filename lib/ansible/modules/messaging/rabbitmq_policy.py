#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2013, John Dewey <john@dewey.ws>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rabbitmq_policy
short_description: Manage the state of policies in RabbitMQ.
description:
  - Manage the state of a policy in RabbitMQ.
version_added: "1.5"
author: "John Dewey (@retr0h)"
options:
  name:
    description:
      - The name of the policy to manage.
    required: true
  vhost:
    description:
      - The name of the vhost to apply to.
    default: /
  apply_to:
    description:
      - What the policy applies to. Requires RabbitMQ 3.2.0 or later.
    default: all
    choices: [all, exchanges, queues]
    version_added: "2.1"
  pattern:
    description:
      - A regex of queues to apply the policy to.
    required: true
  tags:
    description:
      - A dict or string describing the policy.
    required: true
  priority:
    description:
      - The priority of the policy.
    default: 0
  node:
    description:
      - Erlang node name of the rabbit we wish to configure.
    default: rabbit
  state:
    description:
      - The state of the policy.
    default: present
    choices: [present, absent]
'''

EXAMPLES = '''
- name: ensure the default vhost contains the HA policy via a dict
  rabbitmq_policy:
    name: HA
    pattern: .*
  args:
    tags:
      ha-mode: all

- name: ensure the default vhost contains the HA policy
  rabbitmq_policy:
    name: HA
    pattern: .*
    tags:
      ha-mode: all
'''

import json
from ansible.module_utils.basic import AnsibleModule


class RabbitMqPolicy(object):

    def __init__(self, module):
        self._module = module
        self._name = module.params['name']
        self._vhost = module.params['vhost']
        self._pattern = module.params['pattern']
        self._apply_to = module.params['apply_to']
        self._tags = module.params['tags']
        self._priority = module.params['priority']
        self._node = module.params['node']
        self._state = module.params['state']
        self._rabbitmqctl = module.get_bin_path('rabbitmqctl', True)

    def _exec(self, args, run_in_check_mode=False):
        if not self._module.check_mode or (self._module.check_mode and run_in_check_mode):
            cmd = [self._rabbitmqctl, '-q', '-n', self._node]
            args.insert(1, '-p')
            args.insert(2, self._vhost)
            rc, out, err = self._module.run_command(cmd + args, check_rc=True)
            return out.splitlines()
        return list()

    def get(self):
        policies = self._exec(['list_policies'], True)

        for policy in policies:
            if not policy:
                continue
            policy_data = policy.split('\t')
            if policy_data[1] == self._name:
                return dict(
                    apply_to=policy_data[2],
                    pattern=policy_data[3].encode('utf-8').decode('unicode_escape'),  # decode C-escaped string, python 2+3 way
                    tags=json.loads(policy_data[4]),
                    priority=policy_data[5]
                )

    def set(self):
        args = ['set_policy']
        args.append(self._name)
        args.append(self._pattern)
        args.append(json.dumps(self._tags))
        args.append('--priority')
        args.append(self._priority)
        if self._apply_to != 'all':
            args.append('--apply-to')
            args.append(self._apply_to)
        return self._exec(args)

    def clear(self):
        return self._exec(['clear_policy', self._name])

    def run(self):
        result = dict(
            changed=False,
            name=self._name,
            state=self._state
        )

        current_state = self.get()
        exists = current_state is not None

        if exists:
            if self._state == 'absent':
                self.clear()
                result['changed'] = True
            else:
                diffs = [
                    self._apply_to != current_state['apply_to'],
                    self._pattern != current_state['pattern'],
                    self._tags != current_state['tags'],
                    str(self._priority) != str(current_state['priority'])
                ]

                needs_change = any(diffs)
                if needs_change:
                    self.set()

                result['changed'] = needs_change
        elif self._state == 'present':
            self.set()
            result['changed'] = True

        self._module.exit_json(**result)


def main():
    arg_spec = dict(
        name=dict(required=True),
        vhost=dict(default='/'),
        pattern=dict(required=True),
        apply_to=dict(default='all', choices=['all', 'exchanges', 'queues']),
        tags=dict(type='dict', required=True),
        priority=dict(default='0'),
        node=dict(default='rabbit'),
        state=dict(default='present', choices=['present', 'absent']),
    )

    module = AnsibleModule(
        argument_spec=arg_spec,
        supports_check_mode=True
    )

    RabbitMqPolicy(module).run()


if __name__ == '__main__':
    main()
