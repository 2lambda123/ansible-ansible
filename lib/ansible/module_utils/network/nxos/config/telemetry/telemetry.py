#
# -*- coding: utf-8 -*-
# Copyright 2019 Cisco and/or its affiliates.
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
"""
The nxos_telemetry class
It is in this file where the current configuration (as dict)
is compared to the provided configuration (as dict) and the command set
necessary to bring the current configuration to it's desired end-state is
created
"""
import re

from ansible.module_utils.network.common.cfg.base import ConfigBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.network.nxos.facts.facts import Facts
from ansible.module_utils.network.nxos.cmdref.telemetry.telemetry import TMS_GLOBAL, TMS_DESTGROUP, TMS_SENSORGROUP
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import normalize_data, remove_duplicate_context
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import valiate_input, get_setval_path
from ansible.module_utils.network.nxos.utils.telemetry.telemetry import get_module_params_subsection
from ansible.module_utils.network.nxos.nxos import NxosCmdRef, normalize_interface


class Telemetry(ConfigBase):
    """
    The nxos_telemetry class
    """

    gather_subset = [
        '!all',
        '!min',
    ]

    gather_network_resources = [
        'telemetry',
    ]

    def __init__(self, module):
        super(Telemetry, self).__init__(module)

    def get_telemetry_facts(self):
        """ Get the 'facts' (the current configuration)

        :rtype: A dictionary
        :returns: The current configuration as a dictionary
        """
        facts, _warnings = Facts(self._module).get_facts(self.gather_subset, self.gather_network_resources)
        telemetry_facts = facts['ansible_network_resources'].get('telemetry')
        if not telemetry_facts:
            return []
        return telemetry_facts

    def edit_config(self, commands):
        return self._connection.edit_config(commands)

    def execute_module(self):
        """ Execute the module
        :rtype: A dictionary
        :returns: The result from module execution
        """
        result = {'changed': False}
        commands = list()
        warnings = list()
        module_params = self._module.params['config']

        # Normalize interface name.
        int = module_params.get('destination_profile_source_interface')
        if int:
            module_params['destination_profile_source_interface'] = normalize_interface(int)

        existing_telemetry_facts = self.get_telemetry_facts()
        commands.extend(self.set_config(existing_telemetry_facts))
        if commands:
            if not self._module.check_mode:
                self.edit_config(commands)
                #self._connection.load_config(commands)
            result['changed'] = True
        result['commands'] = commands

        changed_telemetry_facts = self.get_telemetry_facts()

        result['before'] = existing_telemetry_facts
        if result['changed']:
            result['after'] = changed_telemetry_facts

        result['warnings'] = warnings
        return result

    def set_config(self, existing_tms_global_facts):
        """ Collect the configuration from the args passed to the module,
            collect the current configuration (as a dict from facts)
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        config = self._module.params['config']
        want = dict((k, v) for k, v in config.items() if v is not None)
        have = existing_tms_global_facts
        resp = self.set_state(want, have)
        return to_list(resp)

    def set_state(self, want, have):
        """ Select the appropriate function based on the state provided
        :param want: the desired configuration as a dictionary
        :param have: the current configuration as a dictionary
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        # Compare want and have states first.  If equal then return.
        state = self._module.params['state']
        if 'overridden' in state or 'replaced' in state:
            self._module.fail_json(msg='State: <{0}> not yet supported'.format(state))

        # Save off module params
        MP = self._module.params['config']

        cmd_ref = {}
        cmd_ref['TMS_GLOBAL'] = {}
        cmd_ref['TMS_DESTGROUP'] = {}
        cmd_ref['TMS_SENSORGROUP'] = {}
        cmd_ref['TMS_SUBSCRIPTION'] = {}

        # Get Telemetry Global Data
        cmd_ref['TMS_GLOBAL']['ref'] = []
        self._module.params['config'][0] = get_module_params_subsection(MP, 'TMS_GLOBAL')
        cmd_ref['TMS_GLOBAL']['ref'].append(NxosCmdRef(self._module, TMS_GLOBAL))
        cmd_ref['TMS_GLOBAL']['ref'][0].set_context()
        cmd_ref['TMS_GLOBAL']['ref'][0].get_existing()
        cmd_ref['TMS_GLOBAL']['ref'][0].get_playvals()
        device_cache = cmd_ref['TMS_GLOBAL']['ref'][0].cache_existing
        if device_cache is None:
            device_cache_lines = []
        else:
            device_cache_lines = device_cache.split("\n")

        # Get Telemetry Destination Group Data
        if want.get('destination_groups'):
            cmd_ref['TMS_DESTGROUP']['ref'] = []
            saved_dest_ids = []
            for playvals in want['destination_groups']:
                valiate_input(playvals, 'destination_groups', self._module)
                if playvals['id'] in saved_dest_ids:
                    continue
                saved_dest_ids.append(playvals['id'])
                resource_key = 'destination-group {0}'.format(playvals['id'])
                self._module.params['config'][0] = get_module_params_subsection(MP, 'TMS_DESTGROUP', playvals['id'])
                cmd_ref['TMS_DESTGROUP']['ref'].append(NxosCmdRef(self._module, TMS_DESTGROUP))
                cmd_ref['TMS_DESTGROUP']['ref'][-1].set_context([resource_key])
                cmd_ref['TMS_DESTGROUP']['ref'][-1].get_existing(device_cache)
                cmd_ref['TMS_DESTGROUP']['ref'][-1].get_playvals()
                normalize_data(cmd_ref['TMS_DESTGROUP']['ref'][-1])

        # Get Telemetry Sensor Group Data
        if want.get('sensor_groups'):
            cmd_ref['TMS_SENSORGROUP']['ref'] = []
            saved_sensor_ids = []
            for playvals in want['sensor_groups']:
                valiate_input(playvals, 'sensor_groups', self._module)
                if playvals['id'] in saved_sensor_ids:
                    continue
                saved_sensor_ids.append(playvals['id'])
                resource_key = 'sensor-group {0}'.format(playvals['id'])
                self._module.params['config'][0] = get_module_params_subsection(MP, 'TMS_SENSORGROUP', playvals['id'])
                cmd_ref['TMS_SENSORGROUP']['ref'].append(NxosCmdRef(self._module, TMS_SENSORGROUP))
                cmd_ref['TMS_SENSORGROUP']['ref'][-1].set_context([resource_key])
                if get_setval_path(self._module):
                    cmd_ref['TMS_SENSORGROUP']['ref'][-1]._ref['path']['setval'] = get_setval_path(self._module)
                cmd_ref['TMS_SENSORGROUP']['ref'][-1].get_existing(device_cache)
                cmd_ref['TMS_SENSORGROUP']['ref'][-1].get_playvals()

        if state == 'overridden':
            if want == have:
                return []
            commands = self._state_overridden(cmd_ref, want, have)
        elif state == 'deleted':
            commands = self._state_deleted(cmd_ref)
        elif state == 'merged':
            if want == have:
                return []
            commands = self._state_merged(cmd_ref)
        elif state == 'replaced':
            if want == have:
                return []
            commands = self._state_replaced(cmd_ref)
        return commands

    @staticmethod
    def _state_overridden(cmd_ref, want, have):
        """ The command generator when state is replaced
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        # remove_keys = set(have) - set(want)
        # add_keys = set(want) - set(have)
        # remove_keys_list = list(remove_keys)
        # add_keys_list = list(add_keys)
        # commands = []
        return commands

    @staticmethod
    def _state_replaced(cmd_ref):
        """ The command generator when state is replaced
        :rtype: A list
        :returns: the commands necessary to migrate the current configuration
                  to the desired configuration
        """
        commands = []
        return commands

    @staticmethod
    def _state_merged(cmd_ref):
        """ The command generator when state is merged
        :rtype: A list
        :returns: the commands necessary to merge the provided into
                  the current configuration
        """
        commands = cmd_ref['TMS_GLOBAL']['ref'][0].get_proposed()

        if cmd_ref['TMS_DESTGROUP'].get('ref'):
            for cr in cmd_ref['TMS_DESTGROUP']['ref']:
                commands.extend(cr.get_proposed())

        if cmd_ref['TMS_SENSORGROUP'].get('ref'):
            for cr in cmd_ref['TMS_SENSORGROUP']['ref']:
                commands.extend(cr.get_proposed())

        return remove_duplicate_context(commands)

    @staticmethod
    def _state_deleted(cmd_ref):
        """ The command generator when state is deleted
        :rtype: A list
        :returns: the commands necessary to remove the current configuration
                  of the provided objects
        """
        commands = cmd_ref['TMS_GLOBAL']['ref'][0].get_proposed()

        if cmd_ref['TMS_DESTGROUP'].get('ref'):
            for cr in cmd_ref['TMS_DESTGROUP']['ref']:
                commands.extend(cr.get_proposed())

        if cmd_ref['TMS_SENSORGROUP'].get('ref'):
            for cr in cmd_ref['TMS_SENSORGROUP']['ref']:
                commands.extend(cr.get_proposed())

        return remove_duplicate_context(commands)
