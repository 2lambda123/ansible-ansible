#
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat Inc.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The ios_acl class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import copy
from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.ios.facts.facts import Facts
from ansible.module_utils.six import iteritems
from ansible.module_utils.network.common.utils import remove_empties
from ansible.module_utils.network.ios.utils.utils import new_dict_to_set


class Acl(ConfigBase):
    """
    The ios_acl class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'acl',
    ]

    def __init__(self, module):
        super(Acl, self).__init__(module)

    def get_acl_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        acl_facts = facts['ansible_network_resources'].get('acl')
        if not acl_facts:
            return []

        return acl_facts

    def execute_module(self):
        """ Execute the module

        :rtype: A dictionary
        :returns: The result from moduel execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()

        if self.state in self.ACTION_STATES:
            existing_acl_facts = self.get_acl_facts()
        else:
            existing_acl_facts = []

        if self.state in self.ACTION_STATES or self.state == 'rendered':
            commands.extend(self.set_config(existing_acl_facts))

        if commands and self.state in self.ACTION_STATES:
            if not self._module.check_mode:
                self._connection.edit_config(commands)
            result['changed'] = True

        if self.state in self.ACTION_STATES:
            result['commands'] = commands

        if self.state in self.ACTION_STATES or self.state == 'gathered':
            changed_acl_facts = self.get_acl_facts()
        elif self.state == 'rendered':
            result['rendered'] = commands
        elif self.state == 'parsed':
            running_config = self._module.params['running_config']
            if not running_config:
                self._module.fail_json(msg="Value of running_config parameter must not be empty for state parsed")
            result['parsed'] = self.get_acl_facts(data=running_config)
        else:
            changed_acl_facts = []

        if self.state in self.ACTION_STATES:
            result['before'] = existing_acl_facts
            if result['changed']:
                result['after'] = changed_acl_facts
        elif self.state == 'gathered':
            result['gathered'] = changed_acl_facts

        result['warnings'] = warnings

        return result

    def set_config(self, existing_acl_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)

        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        want = self._module.params['config']
        have = existing_acl_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        state = self._module.params['state']
        if state in ('overridden', 'merged', 'replaced') and not want:
            self._module.fail_json(msg='value of config parameter must not be empty for state {0}'.format(state))

        if state == 'overridden':
            commands = self._state_overridden(want, have)
        elif state == 'deleted':
            commands = self._state_deleted(want, have)
        elif state == 'merged':
            commands = self._state_merged(want, have)
        elif state == 'replaced':
            commands = self._state_replaced(want, have)

        return commands

    def _state_replaced(self, want, have):
        """ The command generator when state is replaced

        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the deisred configuration
        """
        commands = []

        for config_want in want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('ace'):
                    check = False
                    for config_have in have:
                        for acls_have in config_have.get('acls'):
                            for ace_have in acls_have.get('ace'):
                                if acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    acls_want = remove_empties(acls_want)
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check,
                                                                             "replaced")
                                    if cmd:
                                        if cmd[0] not in commands:
                                            commands.extend(cmd)
                                        temp = self._clear_config(acls_want, config_want)
                                        if temp:
                                            if temp[0] not in commands:
                                                commands.extend(temp)
                                        check = True
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        commands.extend(self._set_config(ace_want,
                                                         {},
                                                         acls_want,
                                                         config_want['afi']))
        commands = self.split_set_cmd(commands)
        commands = [each for each in commands if 'no' in each] + [each for each in commands if 'no' not in each]

        return commands

    def _state_overridden(self, want, have):
        """ The command generator when state is overridden

        :param want: the desired configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        # Creating a copy of want, so that want dict is intact even after delete operation
        # performed during override want n have comparison
        temp_want = copy.deepcopy(want)

        for config_have in have:
            for acls_have in config_have.get('acls'):
                for ace_have in acls_have.get('ace'):
                    check = False
                    for config_want in temp_want:
                        count = 0
                        for acls_want in config_want.get('acls'):
                            for ace_want in acls_want.get('ace'):
                                if acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    acls_want = remove_empties(acls_want)
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check,
                                                                             "overridden")
                                    if cmd:
                                        if cmd[0] not in commands:
                                            commands.extend(cmd)
                                        temp = self._clear_config(acls_want, config_want)
                                        if temp:
                                            if temp[0] not in commands:
                                                commands.extend(temp)
                                        check = True
                                    if check:
                                        del config_want.get('acls')[count]
                                else:
                                    count += 1
                        if check:
                            break
                    if check:
                        break
                if not check:
                    # Delete the config not present in want config
                    commands.extend(self._clear_config(acls_have, config_have))

        # For configuring any non-existing want config
        for config_want in temp_want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('ace'):
                    ace_want = remove_empties(ace_want)
                    commands.extend(self._set_config(ace_want,
                                                     {},
                                                     acls_want,
                                                     config_want['afi']))
        # Split and arrange the config commands
        commands = self.split_set_cmd(commands)
        # Arranging the cmds suct that all delete cmds are fired before all set cmds
        commands = [each for each in commands if 'no' in each] + [each for each in commands if 'no' not in each]

        return commands

    def _state_merged(self, want, have):
        """ The command generator when state is merged

        :param want: the additive configuration as a dictionary
        :param obj_in_have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = []

        for config_want in want:
            for acls_want in config_want.get('acls'):
                for ace_want in acls_want.get('ace'):
                    check = False
                    for config_have in have:
                        for acls_have in config_have.get('acls'):
                            for ace_have in acls_have.get('ace'):
                                if acls_want.get('name') == acls_have.get('name'):
                                    ace_want = remove_empties(ace_want)
                                    cmd, check = self.common_condition_check(ace_want,
                                                                             ace_have,
                                                                             acls_want,
                                                                             config_want,
                                                                             check)
                                    commands.extend(cmd)
                            if check:
                                break
                        if check:
                            break
                    if not check:
                        # For configuring any non-existing want config
                        ace_want = remove_empties(ace_want)
                        commands.extend(self._set_config(ace_want,
                                                         {},
                                                         acls_want,
                                                         config_want['afi']))
        commands = self.split_set_cmd(commands)

        return commands

    def _state_deleted(self, want, have):
        """ The command generator when state is deleted

        :param want: the objects from which the configuration should be removed
        :param obj_in_have: the current configuration as a dictionary
        :param interface_type: interface type
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = []
        if want:
            for config_want in want:
                for acls_want in config_want.get('acls'):
                    for config_have in have:
                        for acls_have in config_have.get('acls'):
                            if acls_want.get('name') == acls_have.get('name'):
                                commands.extend(self._clear_config(acls_want, config_want))
        else:
            for config_have in have:
                for acls_have in config_have.get('acls'):
                    commands.extend(self._clear_config(acls_have, config_have))

        return commands

    def common_condition_check(self, want, have, acls_want, config_want, check, state=''):
        """ The command formatter from the generated command
        :param want: want config
        :param have: have config
        :param acls_want: acl want config
        :param config_want: want config list
        :param check: for same acl in want and have config, check=True
        :param state: operation state
        :rtype: A list
        :returns: commands generated from want n have config diff
        """
        commands = []
        if want.get('destination') and have.get('destination') or \
                want.get('source').get('address') and have.get('source'):
            if want.get('destination').get('address') == \
                    have.get('destination').get('address') and \
                    want.get('source').get('address') == \
                    have.get('source').get('address'):
                check = True
                commands.extend(self._set_config(want,
                                                 have,
                                                 acls_want,
                                                 config_want['afi']))
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(acls_want, config_want))
            elif want.get('destination').get('any') == \
                    have.get('destination').get('any') and \
                    want.get('source').get('address') == \
                    have.get('source').get('address') and \
                    want.get('destination').get('any'):
                check = True
                commands.extend(self._set_config(want,
                                                 have,
                                                 acls_want,
                                                 config_want['afi']))
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(acls_want, config_want))
            elif want.get('destination').get('address') == \
                    have.get('destination').get('address') and \
                    want.get('source').get('any') == have.get('source').get('any') and \
                    want.get('source').get('any'):
                check = True
                commands.extend(self._set_config(want,
                                                 have,
                                                 acls_want,
                                                 config_want['afi']))
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(acls_want, config_want))
            elif want.get('destination').get('any') == \
                    have.get('destination').get('any') and \
                    want.get('source').get('any') == have.get('source').get('any') and \
                    want.get('destination').get('any'):
                check = True
                commands.extend(self._set_config(want,
                                                 have,
                                                 acls_want,
                                                 config_want['afi']))
                if commands:
                    if state == 'replaced' or state == 'overridden':
                        commands.extend(self._clear_config(acls_want, config_want))

        return commands, check

    def split_set_cmd(self, cmds):
        """ The command formatter from the generated command
        :param cmds: generated command
        :rtype: A list
        :returns: the formatted commands which is compliant and
        actually fired on the device
        """
        command = []

        def common_code(access_grant, cmd, command):
            cmd = cmd.split(access_grant)
            access_list = cmd[0].strip(' ')
            if access_list not in command:
                command.append(access_list)
            index = command.index(access_list) + 1
            cmd = access_grant + cmd[1]
            command.insert(index + 1, cmd)

        for each in cmds:
            if 'no' in each:
                command.append(each)
            if 'deny' in each:
                common_code('deny', each, command)
            if 'permit' in each:
                common_code('permit', each, command)

        return command

    def source_dest_config(self, config, cmd, protocol_option):
        """ Function to populate source/destination address and port protocol options
        :param config: want and have diff config
        :param cmd: source/destination command
        :param protocol_option: source/destination protocol option
        :rtype: A list
        :returns: the commands generated based on input source/destination params
        """
        if 'ipv6' in cmd:
            address = config.get('address')
            if address and '::' not in address:
                self._module.fail_json(msg='Incorrect IPV6 address!')
        else:
            address = config.get('address')
            wildcard = config.get('wildcard_bits')
        any = config.get('any')
        if address and wildcard:
            cmd = cmd + ' {0} {1}'.format(address, wildcard)
        if any:
            cmd = cmd + ' {0}'.format('any')
        port_protocol = config.get('port_protocol')
        if port_protocol and (protocol_option.get('tcp') or protocol_option.get('udp')):
            cmd = cmd + ' {0} {1}'.format(list(port_protocol)[0], list(port_protocol.values())[0])
        elif port_protocol and not (protocol_option.get('tcp') or protocol_option.get('udp')):
            self._module.fail_json(msg='Port Protocol option is valid only with TCP/UDP Protocol option!')

        return cmd

    def _set_config(self, want, have, acl_want, afi):
        """ Function that sets the interface config based on the want and have config
        :param want: want config
        :param have: have config
        :param acl_want: want acl config
        :param afi: acl afi type
        :rtype: A list
        :returns: the commands generated based on input want/have params
        """
        commands = []
        want_set = set()
        have_set = set()
        # Convert the want and have dict to its respective set for taking the set diff
        new_dict_to_set(want, [], want_set)
        new_dict_to_set(have, [], have_set)
        diff = want_set - have_set
        # Populate the config only when there's a diff b/w want and have config
        if diff:
            name = acl_want.get('name')
            if afi == 'ipv4':
                try:
                    name = int(name)
                    # If name is numbered acl
                    if name <= 99:
                        cmd = 'ip access-list standard {0}'.format(name)
                    elif name >= 100:
                        cmd = 'ip access-list extended {0}'.format(name)
                except ValueError:
                    # If name is named acl
                    acl_type = acl_want.get('acl_type')
                    if acl_type:
                        cmd = 'ip access-list {0} {1}'.format(acl_type, name)
                    else:
                        self._module.fail_json(msg='ACL type value is required for Named ACL!')

            elif afi == 'ipv6':
                cmd = 'ipv6 access-list {0}'.format(name)

            # Get all of ace option values from diff dict
            grant = want.get('grant')
            source = want.get('source')
            destination = want.get('destination')
            po = want.get('protocol_options')
            dscp = want.get('dscp')
            fragments = want.get('fragments')
            log = want.get('log')
            log_input = want.get('log_input')
            option = want.get('option')
            precedence = want.get('precedence')
            time_range = want.get('time_range')
            tos = want.get('tos')
            ttl = want.get('ttl')

            if grant:
                cmd = cmd + ' {0}'.format(grant)
            if po and isinstance(po, dict):
                po_key = list(po)[0]
                cmd = cmd + ' {0}'.format(po_key)
                if po.get('icmp'):
                    po_val = po.get('icmp')
                elif po.get('igmp'):
                    po_val = po.get('igmp')
                elif po.get('tcp'):
                    po_val = po.get('tcp')
            if source:
                cmd = self.source_dest_config(source, cmd, po)
            if destination:
                cmd = self.source_dest_config(destination, cmd, po)
            if po_val:
                cmd = cmd + ' {0}'.format(list(po_val)[0])
            if dscp:
                cmd = cmd + ' dscp {0}'.format(dscp)
            if fragments:
                cmd = cmd + ' fragments {0}'.format(fragments)
            if log:
                cmd = cmd + ' log {0}'.format(log)
            if log_input:
                cmd = cmd + ' log-input {0}'.format(log_input)
            if option:
                cmd = cmd + ' option {0}'.format(list(option)[0])
            if precedence:
                cmd = cmd + ' precedence {0}'.format(precedence)
            if time_range:
                cmd = cmd + ' time-range {0}'.format(time_range)
            if tos:
                for k, v in iteritems(tos):
                    if k == 'service_value':
                        cmd = cmd + ' tos {0}'.format(v)
                    else:
                        cmd = cmd + ' tos {0}'.format(v)
            if ttl:
                for k, v in iteritems(ttl):
                    if k == 'range' and v:
                        start = v.get('start')
                        end = v.get('start')
                        cmd = cmd + ' ttl {0} {1}'.format(start, end)
                    elif v:
                        cmd = cmd + ' ttl {0} {1}'.format(k, v)

            commands.append(cmd)

        return commands

    def _clear_config(self, acl, config):
        """ Function that deletes the acl config based on the want and have config
        :param acl: acl config
        :param config: config
        :rtype: A list
        :returns: the commands generated based on input acl/config params
        """
        commands = []
        afi = config.get('afi')
        name = acl.get('name')
        if afi == 'ipv4':
            try:
                name = int(name)
                if name <= 99:
                    cmd = 'no ip access-list standard {0}'.format(name)
                elif name >= 100:
                    cmd = 'no ip access-list extended {0}'.format(name)
            except ValueError:
                acl_type = acl.get('acl_type')
                if acl_type == 'extended':
                    cmd = 'no ip access-list extended {0}'.format(name)
                elif acl_type == 'standard':
                    cmd = 'no ip access-list standard {0}'.format(name)
                else:
                    self._module.fail_json(msg="ACL type value is required for Named ACL!")
        elif afi == 'ipv6':
            cmd = 'no ipv6 access-list {0}'.format(name)
        commands.append(cmd)

        return commands
