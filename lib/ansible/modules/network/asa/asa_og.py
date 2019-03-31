#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: asa_og
version_added: "2.8"
author:
    - "Federico Olivieri (@Federico87)"
short_description: Manage object groups on a Cisco ASA
description:
    - This module allows you to create and update object-group network/service on Cisco ASA device.
extends_documentation_fragment: asa
options:
    description:
        description:
            - object-group description
    name:
        description:
            - object-group name
        required: true
    state:
        description:
            - Manage the state of the resource.
        default: replace
        choices: ['present', 'absent', 'replace']
    group_type:
        description:
            - object-group type
        choices: ['network-object', 'service-object', 'port-object']
        required: true
    protocol:
        description:
            - protocol for object-group service with port-object
        choices: ['udp', 'tcp', 'tcp-udp']
    lines:
        description:
            - config lines for objecrt-group entries
        required: true
        type: list
"""

EXAMPLES = """
# Note: examples below use the following provider dict to handle
#       transport and authentication to the node.
---
- name: configure UDP object-group service with port-object
  asa_og:
    name: service_object_test
    group_type: port-object
    protocol: udp
    state: replace
    description: this is an 3x4mpl3
    lines: ['range 56832 56959', 'range 61363 65185']
    provider: "{{ fws }}"
  register: result
"""

RETURN = """
commands:
  description: command sent to the device
  returned: always
  type: list
  sample: [
    "object-group service service_object_test udp",
    "description this is an 3x4mpl3",
    " port-object range 56832 56959",
    " port-object range 61363 65185"
    ]
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.asa.asa import asa_argument_spec, check_args
from ansible.module_utils.network.asa.asa import get_config, load_config, run_commands
from ansible.module_utils.network.common.config import NetworkConfig, dumps
import re
import sys
__metaclass__ = type


class Parser():
    '''Regex class for outputs parsing'''

    def __init__(self, config, protocol):
        '''Parser __init__ method'''
        self.config = config
        self.protocol = protocol

    def parse_obj_grp(self):
        grp_list = list()
        match = re.findall(r'(?:network-object\s|port-object\s|service-object\s)(.*)|(group-object\s.*)', self.config, re.M)
        if match:
            for i in match:
                if i[0]:
                    grp_list.append(i[0])
                elif i[1]:
                    grp_list.append(i[1])

            return grp_list

    def parse_obj_grp_name(self):
        list_return = list()
        match = re.search(r'(?:object-group\s)(network\s|service\s)(\w+)\s?(tcp|udp)?', self.config, re.M)

        if match:
            if match.group(3):
                list_return.append(True)
            else:
                list_return.append(False)

            if match.group(2):
                list_return.append(str(match.group(2)))

            if match.group(1):
                list_return.append(str(match.group(1)))

        return list_return

    def parse_obj_grp_description(self):
        match = re.search(r'(description\s)(.*)', self.config, re.M)
        if match:
            description = match.group(2)

            return description


def map_config_to_obj(module):

    obj = list()
    obj_dict = dict()

    group_type = module.params['group_type']
    group_name = module.params['name']
    protocol = module.params['protocol']

    sh_run_group_name = get_config(module, flags=['object-group | include {0}'.format(group_name)])
    run_group_name = Parser(sh_run_group_name, protocol).parse_obj_grp_name()

    obj_dict['have_name'] = run_group_name

    if run_group_name:
        if run_group_name[0] is True:
            obj_dict['have_group_type'] = "port-object"
        elif 'network' in run_group_name[2]:
            obj_dict['have_group_type'] = "network-object"
        elif 'service' in run_group_name[2] and run_group_name[0] is False:
            obj_dict['have_group_type'] = "service-object"

    sh_run_group_type = get_config(module, flags=['object-group id {0}'.format(group_name)])
    have_description = Parser(sh_run_group_type, protocol).parse_obj_grp_description()
    obj_dict['have_description'] = have_description

    if group_type == 'network-object':
        sh_run_group_type = get_config(module, flags=['object-group id {0}'.format(group_name)])
        have_lines = Parser(sh_run_group_type, protocol).parse_obj_grp()

        obj_dict['have_lines'] = have_lines

    elif group_type == 'service-object' or group_type == 'port-object':
        sh_run_group_type = get_config(module, flags=['object-group id {0}'.format(group_name)])
        have_lines_raw = Parser(sh_run_group_type, protocol).parse_obj_grp()

        if have_lines_raw:
            have_lines = list()
            for i in have_lines_raw:
                have_lines.append(i.rstrip(' '))
            obj_dict['have_lines'] = have_lines
        elif have_lines_raw is None:
            obj_dict['have_lines'] = have_lines_raw

    obj.append(obj_dict)

    return obj


def replace(want_dict):

    commands = list()
    add_lines = list()
    remove_lines = list()

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    lines = want_dict['lines']
    description = want_dict['description']

    if have_config:
        if description and description != have_description:
            if 'network-object' in group_type and 'network' in have_group_type:
                commands.append('object-group network {0}'.format(name))
                commands.append('description {0}'.format(description))
            elif 'service-object' in group_type and 'service' in have_group_type:
                commands.append('object-group service {0}'.format(name))
                commands.append('description {0}'.format(description))
            elif 'service-object' in group_type and 'service' in have_group_type:
                commands.append('object-group service {0}'.format(name))
                commands.append('description {0}'.format(description))

        if lines != sorted(have_config):
            if have_group_type:
                if 'network-object' in group_type and 'network' in have_group_type:
                    commands.append('object-group network {0}'.format(name))
                    for i in lines:
                        if i not in have_config:
                            if 'object' not in i:
                                add_lines.append('network-object ' + i)
                            else:
                                add_lines.append(i)

                    for i in have_config:
                        if i not in lines:
                            if 'group-object' not in i:
                                remove_lines.append('no network-object ' + i)
                            else:
                                remove_lines.append('no ' + i)

                elif 'service-object' in group_type and 'service' in have_group_type:
                    commands.append('object-group service {0}'.format(name))
                    for i in lines:
                        if i not in have_config:
                            if 'group-object' not in i:
                                add_lines.append('service-object ' + i)
                            else:
                                add_lines.append(i)

                    for i in have_config:
                        if i not in lines:
                            if 'group-object' not in i:
                                remove_lines.append('no service-object ' + i)
                            else:
                                remove_lines.append('no ' + i)

                elif 'port-object' in group_type and 'port' in have_group_type:
                    commands.append('object-group service {0} {1}'.format(name, protocol))
                    for i in lines:
                        if i not in have_config:
                            if 'group-object' not in i:
                                add_lines.append('port-object ' + i)
                            else:
                                add_lines.append(i)

                    for i in have_config:
                        if i not in lines:
                            if 'group-object' not in i:
                                remove_lines.append('no port-object ' + i)
                            else:
                                add_lines.append(i)

                set_add_lines = set(add_lines)
                set_remove_lines = set(remove_lines)

                for i in list(set_add_lines) + list(set_remove_lines):
                    commands.append(i)

    elif have_config is None and have_group_type is None:

        if 'network-object' in group_type:
            commands.append('object-group network {0}'.format(name))

            if description and have_description is None:
                commands.append('description {0}'.format(description))

            for i in lines:
                if 'object' not in i:
                    add_lines.append('network-object ' + i)
                else:
                    add_lines.append(i)

            for i in set(add_lines):
                commands.append(i)

        elif 'service-object' in group_type:
            commands.append('object-group service {0}'.format(name))

            if description and have_description is None:
                commands.append('description {0}'.format(description))

            for i in lines:
                add_lines.append('service-object ' + i)

            for i in set(add_lines):
                commands.append(i)

        elif 'port-object' in group_type:
            commands.append('object-group service {0} {1}'.format(name, protocol))

            if description and have_description is None:
                commands.append('description {0}'.format(description))

            for i in lines:
                add_lines.append('port-object ' + i)

            for i in set(add_lines):
                commands.append(i)

    return commands


def present(want_dict):

    commands = list()
    add_lines = list()
    remove_lines = list()

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    lines = want_dict['lines']
    description = want_dict['description']

    if have_config:
        if have_group_type:
            if 'network-object' in group_type and 'network' in have_group_type:

                if description:
                    if have_description is None or have_description != description:
                        commands.append('object-group network {0}'.format(name))
                        commands.append('description {0}'.format(description))

                for i in lines:
                    if i not in have_config:
                        if 'object-group network {0}'.format(name) not in commands:
                            commands.append('object-group network {0}'.format(name))

                        if 'object' not in i:
                            add_lines.append('network-object ' + i)
                        else:
                            add_lines.append(i)

            elif 'service-object' in group_type and 'service' in have_group_type and name not in have_name:

                if description:
                    if have_description is None or have_description != description:
                        commands.append('object-group service {0}'.format(name))
                        commands.append('description {0}'.format(description))

                for i in lines:
                    if i not in have_config:
                        if 'object-group service {0}'.format(name) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        if 'group-object' not in i:
                            add_lines.append('service-object ' + i)
                        else:
                            add_lines.append(i)

            elif 'port-object' in group_type and 'port' in have_group_type and name not in have_name:

                if description:
                    if have_description is None or have_description != description:
                        commands.append('object-group service {0} {1}'.format(name, protocol))
                        commands.append('description {0}'.format(description))

                for i in lines:
                    if i not in have_config:
                        if 'object-group service {0} {1}'.format(name, protocol) not in commands:
                            commands.append('object-group service {0}'.format(name))
                        if 'group-object' not in i:
                            add_lines.append('port-object ' + i)
                        else:
                            add_lines.append(i)

            set_add_lines = set(add_lines)

            for i in list(set_add_lines):
                commands.append(i)

    elif have_config is None or have_group_type is None:

        if 'network-object' in group_type:
            commands.append('object-group network {0}'.format(name))

            if description:
                if have_description is None or have_description != description:
                    commands.append('description {0}'.format(description))

            for i in lines:
                if 'object' not in i:
                    add_lines.append('network-object ' + i)
                else:
                    add_lines.append(i)
            for i in set(add_lines):
                commands.append(i)

        elif 'service-object' in group_type:
            commands.append('object-group service {0}'.format(name))

            if description:
                if have_description is None or have_description != description:
                    commands.append('description {0}'.format(description))

            for i in lines:
                add_lines.append('service-object ' + i)

            for i in set(add_lines):
                commands.append(i)

        elif 'port-object' in group_type:
            commands.append('object-group service {0} {1}'.format(name, protocol))

            if description:
                if have_description is None or have_description != description:
                    commands.append('description {0}'.format(description))

            for i in lines:
                add_lines.append('port-object ' + i)

            for i in set(add_lines):
                commands.append(i)

    return commands


def absent(want_dict):

    commands = list()
    add_lines = list()
    remove_lines = list()

    name = want_dict['name']
    group_type = want_dict['group_type']
    protocol = want_dict['protocol']
    lines = want_dict['lines']
    description = want_dict['description']

    if have_config:
        if have_group_type:
            if 'network-object' in group_type and 'network' in have_group_type:
                commands.append('object-group network {0}'.format(name))

                if description and description == have_description:
                    commands.append('no description {0}'.format(description))

                for i in lines:
                    if i in have_config:
                        if 'object' not in i:
                            add_lines.append('no network-object ' + i)
                        else:
                            add_lines.append('no ' + i)

            elif 'service-object' in group_type and 'service' in have_group_type:
                commands.append('object-group service {0}'.format(name))

                if description and description == have_description:
                    commands.append('no description {0}'.format(description))

                for i in lines:
                    if i in have_config:
                        if 'group-object' not in i:
                            add_lines.append('no service-object ' + i)
                        else:
                            add_lines.append('no ' + i)

            elif 'port-object' in group_type and 'port' in have_group_type:
                commands.append('object-group service {0} {1}'.format(name, protocol))

                if description and description == have_description:
                    commands.append('no description {0}'.format(description))

                for i in lines:
                    if i in have_config:
                        if 'group-object' not in i:
                            add_lines.append('no port-object ' + i)
                        else:
                            add_lines.append('no ' + i)

            set_add_lines = set(add_lines)

            for i in list(set_add_lines):
                commands.append(i)

    return commands


def map_obj_to_commands(want, have, module):

    global have_name
    have_name = have[0].get('have_name')
    global have_group_type
    have_group_type = have[0].get('have_group_type')
    global have_config
    have_config = have[0].get('have_lines')
    global have_description
    have_description = have[0].get('have_description')

    for w in want:
        want_dict = dict()

        want_dict['name'] = w['name']
        want_dict['group_type'] = w['group_type']
        want_dict['protocol'] = w['protocol']
        want_dict['lines'] = sorted(set(w['lines']))
        want_dict['description'] = w['description']
        state = w['state']

        if state == 'replace':
            return replace(want_dict)
        elif state == 'present':
            return present(want_dict)
        elif state == 'absent':
            return absent(want_dict)


def map_params_to_obj(module):

    obj = list()

    obj.append({
        'name': module.params['name'],
        'group_type': module.params['group_type'],
        'protocol': module.params['protocol'],
        'lines': module.params['lines'],
        'state': module.params['state'],
        'description': module.params['description']
    })

    return obj


def main():

    argument_spec = dict(
        name=dict(required=True),
        group_type=dict(choices=['network-object', 'service-object', 'port-object'], required=True),
        protocol=dict(choices=['udp', 'tcp', 'tcp-udp']),
        lines=dict(type='list', required=True),
        description=dict(),
        state=dict(choices=['present', 'absent', 'replace'], default='replace')
    )

    argument_spec.update(asa_argument_spec)
    required_if = [('group_type', 'port-object', ['protocol'])]

    module = AnsibleModule(argument_spec=argument_spec,
                           required_if=required_if,
                           supports_check_mode=True)

    result = {'changed': False}

    want = map_params_to_obj(module)
    have = map_config_to_obj(module)
    config_commans = map_obj_to_commands(want, have, module)

    result['commands'] = config_commans
    result['have'] = have
    result['want'] = want

    if config_commans:
        if not module.check_mode:
            load_config(module, config_commans)
        result['changed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
