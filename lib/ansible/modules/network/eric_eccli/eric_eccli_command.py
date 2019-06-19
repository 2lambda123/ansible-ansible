#!/usr/bin/python
#
# Copyright (c) 2019 Ericsson AB.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#


from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = """
---
module: eric_eccli_command
version_added: "2.9"
author: Ericsson IPOS OAM team (@cheng.you@ericsson.com)
short_description: Run commands on remote devices running Ericsson ECCLI
description:
  - Sends arbitrary commands to an ERICSSON eccli node and returns the results
    read from the device. This module includes an
    argument that will cause the module to wait for a specific condition
    before returning or timing out if the condition is not met.
  - This module also supports running commands in configuration mode
    in raw command style.
notes:
  - Tested against IPOS 19.3
"""

EXAMPLES = r"""
tasks:
  - name: run show version on remote devices
    eric_eccli_command:
      commands: show version

  - name: run show version and check to see if output contains IPOS
    eric_eccli_command:
      commands: show version
      wait_for: result[0] contains IPOS

  - name: run multiple commands on remote nodes
    eric_eccli_command:
      commands:
        - show version
        - show running-config interfaces

  - name: run multiple commands and evaluate the output
    eric_eccli_command:
      commands:
        - show version
        - show running-config interfaces
      wait_for:
        - result[0] contains IPOS
        - result[1] contains management

  - name: run commands that require answering a prompt
    eric_eccli_command:
      commands:
        - command: 'config'
        - command: 'system hostname ub4-1-changed'
        - command: 'commit'
          prompt: 'Uncommitted changes found, commit them? [yes/no/CANCEL]'
          answer: 'no'
        - command: 'end'

  - name: Set the prompt and error information regular expressions
    eric_eccli_command:
      commands:
        - command: 'evr_2d01_vfrwd-evr1#dd'
          prompt: 'error input: element does not exist'
        - ansible.cfg:
        - command: '[\r\n]+ error input: .*'

        - command: 'evr_2d01_vfrwd-evr1#aaa'
          prompt: 'aaa#'
        - ansible.cfg:
        - command: 'a{3}?#'
"""

RETURN = """
stdout:
  description: The set of responses from the commands
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: ['...', '...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low level errors (such as action plugin)
  type: list
  sample: [['...', '...'], ['...'], ['...']]
failed_conditions:
  description: The list of conditionals that have failed
  returned: failed
  type: list
  sample: ['...', '...']
"""
import re
import time

from ansible.module_utils._text import to_text
from ansible.module_utils.network.eric_eccli.eric_eccli import run_commands
from ansible.module_utils.network.eric_eccli.eric_eccli import eric_eccli_argument_spec
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.utils import transform_commands
from ansible.module_utils.network.common.parsing import Conditional
from ansible.module_utils.six import string_types


def to_lines(stdout):
    for item in stdout:
        if isinstance(item, string_types):
            item = str(item).split('\n')
        yield item


def parse_commands(module, warnings):
    commands = transform_commands(module)

    for item in list(commands):
        if module.check_mode:
            if item['command'].startswith('conf'):
                warnings.append(
                    'only non-config commands are supported when using check mode, not '
                    'executing %s' % item['command']
                )
                commands.remove(item)
    return commands


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        commands=dict(type='list', required=True),

        wait_for=dict(type='list', aliases=['waitfor']),
        match=dict(default='all', choices=['all', 'any']),

        retries=dict(default=10, type='int'),
        interval=dict(default=1, type='int')
    )

    argument_spec.update(eric_eccli_argument_spec)

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    result = {'changed': False}

    warnings = list()
    commands = parse_commands(module, warnings)
    result['warnings'] = warnings

    wait_for = module.params['wait_for'] or list()
    conditionals = [Conditional(c) for c in wait_for]

    retries = module.params['retries']
    interval = module.params['interval']
    match = module.params['match']

    while retries > 0:
        responses = run_commands(module, commands)

        for item in list(conditionals):
            if item(responses):
                if match == 'any':
                    conditionals = list()
                    break
                conditionals.remove(item)

        if not conditionals:
            break

        time.sleep(interval)
        retries -= 1

    if conditionals:
        failed_conditions = [item.raw for item in conditionals]
        msg = 'One or more conditional statements have not been satisfied'
        module.fail_json(msg=msg, failed_conditions=failed_conditions)

    result.update({
        'changed': False,
        'stdout': responses,
        'stdout_lines': list(to_lines(responses))
    })

    module.exit_json(**result)


if __name__ == '__main__':
    main()
