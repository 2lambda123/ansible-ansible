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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: vyos_command
version_added: "2.2"
author: "Nathaniel Case (@qalthos)"
short_description: Run one or more commands on VyOS devices
description:
  - The command module allows running one or more commands on remote
    devices running VyOS.  This module can also be introspected
    to validate key parameters before returning successfully.  If the
    conditional statements are not met in the wait period, the task
    fails.
  - Certain C(show) commands in VyOS produce many lines of output and
    use a custom pager that can cause this module to hang.  If the
    value of the environment variable C(ANSIBLE_VYOS_TERMINAL_LENGTH)
    is not set, the default number of 10000 is used.
extends_documentation_fragment: vyos
options:
  commands:
    description:
      - The ordered set of commands to execute on the remote device
        running VyOS.  The output from the command execution is
        returned to the playbook.  If the I(wait_for) argument is
        provided, the module is not returned until the condition is
        satisfied or the number of retries has been exceeded.
    required: true
  wait_for:
    description:
      - Specifies what to evaluate from the output of the command
        and what conditionals to apply.  This argument will cause
        the task to wait for a particular conditional to be true
        before moving forward.  If the conditional is not true
        by the configured I(retries), the task fails. See examples.
    required: false
    default: null
    aliases: ['waitfor']
  match:
    description:
      - The I(match) argument is used in conjunction with the
        I(wait_for) argument to specify the match policy. Valid
        values are C(all) or C(any).  If the value is set to C(all)
        then all conditionals in the wait_for must be satisfied.  If
        the value is set to C(any) then only one of the values must be
        satisfied.
    required: false
    default: all
    choices: ['any', 'all']
  retries:
    description:
      - Specifies the number of retries a command should be tried
        before it is considered failed. The command is run on the
        target device every retry and evaluated against the I(wait_for)
        conditionals.
    required: false
    default: 10
  interval:
    description:
      - Configures the interval in seconds to wait between I(retries)
        of the command. If the command does not pass the specified
        conditions, the interval indicates how long to wait before
        trying the command again.
    required: false
    default: 1

notes:
  - Tested against VYOS 1.1.7
  - Running C(show system boot-messages all) will cause the module to hang since
    VyOS is using a custom pager setting to display the output of that command.
"""

EXAMPLES = """
tasks:
  - name: show configuration on ethernet devices eth0 and eth1
    vyos_command:
      commands:
        - show interfaces ethernet {{ item }}
    with_items:
      - eth0
      - eth1

  - name: run multiple commands and check if version output contains specific version string
    vyos_command:
      commands:
        - show version
        - show hardware cpu
      wait_for:
        - "result[0] contains 'VyOS 1.1.7'"
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
warnings:
  description: The list of warnings (if any) generated by module based on arguments
  returned: always
  type: list
  sample: ['...', '...']
"""
import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
from ansible.module_utils.netcli import Conditional
from ansible.module_utils.network_common import ComplexList
from ansible.module_utils.six import string_types
from ansible.module_utils.vyos import run_commands
from ansible.module_utils.vyos import vyos_argument_spec


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def parse_commands(module, warnings):
    command = ComplexList(dict(
        command=dict(key=True),
        prompt=dict(),
        answer=dict(),
    ), module)
    commands = command(module.params['commands'])
    items = []

    for item in commands:
        if module.check_mode and not item['command'].startswith('show'):
            warnings.append('only show commands are supported when using '
                            'check mode, not executing `%s`' % item['command'])
        else:
            items.append(module.jsonify(item))

    return items


def main():
    spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    spec.update(vyos_argument_spec)

    module = AnsibleModule(argument_spec=spec, supports_check_mode=True)

    warnings = list()

    commands = parse_commands(module, warnings)

    wait_for = module.params['wait_for'] or list()
    try:
        conditionals = [Conditional(c) for c in wait_for]
    except AttributeError:
        exc = get_exception()
        module.fail_json(msg=str(exc))

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    for _ in range(retries):
        responses = run_commands(module, commands)

        for item in conditionals:
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

            if not conditionals:
                break

            time.sleep(interval)

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, falied_conditions=failed_conditions)

    result = {
        'changed': False,
        'stdout': responses,
        'warnings': warnings,
        'stdout_lines': list(to_lines(responses)),
    }

    module.exit_json(**result)


if __name__ == '__main__':
    main()
