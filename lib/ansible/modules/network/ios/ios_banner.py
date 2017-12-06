#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: ios_banner
version_added: "2.3"
author:
- Ricardo Carrillo Cruz (@rcarrillocruz)
short_description: Manage multiline banners on Cisco IOS devices
description:
  - This will configure both login and motd banners on remote devices
    running Cisco IOS.  It allows playbooks to add or remote
    banner text from the active running configuration.
extends_documentation_fragment: ios
notes:
  - Tested against IOS 15.6
options:
  banner:
    description:
      - Specifies which banner that should be
        configured on the remote device.
    required: true
    choices: [ login,  motd ]
  text:
    description:
      - The banner text that should be
        present in the remote device running configuration.  This argument
        accepts a multiline string, with no empty lines. Requires I(state=present).
  state:
    description:
      - Specifies whether or not the configuration is
        present in the current devices active running configuration.
    default: present
    choices: [ absent, present ]
"""

EXAMPLES = """
- name: configure the login banner
  ios_banner:
    banner: login
    text: |
      this is my login banner
      that contains a multiline
      string
    state: present

- name: remove the motd banner
  ios_banner:
    banner: motd
    state: absent

- name: Configure banner from file
  ios_banner:
    banner:  motd
    text: "{{ lookup('file', './config_partial/raw_banner.cfg') }}"
    state: present

"""

RETURN = """
commands:
  description: The list of configuration mode commands to send to the device
  returned: always
  type: list
  sample:
    - banner login
    - this is my login banner
    - that contains a multiline
    - string
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.connection import exec_command
from ansible.module_utils.network.ios.ios import check_args, ios_argument_spec, load_config, run_commands
import re


def map_obj_to_commands(updates, module):
    commands = list()
    want, have = updates
    state = module.params['state']

    if state == 'absent' and 'text' in have.keys() and have['text']:
        commands.append('no banner %s' % module.params['banner'])

    elif state == 'present':
        if want['text'] and (want['text'] != have.get('text')):
            banner_cmd = 'banner %s' % module.params['banner']
            banner_cmd += ' @\n'
            banner_cmd += want['text'].strip()
            banner_cmd += '\n@'
            commands.append(banner_cmd)

    return commands


def map_config_to_obj(module):
    rc, out, err = exec_command(module, 'show banner %s' % module.params['banner'])
    if rc == 0:
        output = out
    else:
        rc, out, err = exec_command(module,
                                    'show running-config | begin banner %s'
                                    % module.params['banner'])
        if out:
            output = re.search(r'\^C(.*)\^C', out, re.S).group(1).strip()
        else:
            output = None
    obj = {'banner': module.params['banner'], 'state': 'absent'}
    if output:
        obj['text'] = output
        obj['state'] = 'present'
    return obj


def map_params_to_obj(module):
    text = module.params['text']
    if text:
        text = str(text).strip()

    return {
        'banner': module.params['banner'],
        'text': text,
        'state': module.params['state']
    }


def main():
    """ main entry point for module execution
    """
    argument_spec = dict(
        banner=dict(type='str', required=True, choices=['login', 'motd']),
        text=dict(type='str'),
        state=dict(type='str', default='present', choices=['absent', 'present']),
    )

    argument_spec.update(ios_argument_spec)

    required_if = [('state', 'present', ('text',))]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    warnings = list()
    check_args(module, warnings)

    result = {'changed': False}
    if warnings:
        result['warnings'] = warnings
    want = map_params_to_obj(module)
    have = map_config_to_obj(module)

    commands = map_obj_to_commands((want, have), module)
    result['commands'] = commands

    if commands:
        if not module.check_mode:
            response = load_config(module, commands)

        result['changed'] = True

    module.exit_json(**result)

if __name__ == '__main__':
    main()
