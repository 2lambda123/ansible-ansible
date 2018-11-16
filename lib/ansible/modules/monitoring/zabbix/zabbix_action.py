#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)


from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: zabbix_action

short_description: Create/Delete/Update Zabbix actions

version_added: "2.4"

description:
    - This module allows you to create, modify and delete Zabbix actions.

options:
    name:
        description:
            - Name of the action
        required: true
    event_source:
        description:
            - Type of events that the action will handle.
        required: true
        choices: ['trigger', 'discovery', 'auto_registration', 'internal']
    state:
        description:
            - State of the action.
            - On C(present), it will create an action if it does not exist or update the action if the associated data is different.
            - On C(absent), it will remove the action if it exists.
        choices: ['present', 'absent']
        default: 'present'
    status:
        description:
            - Monitoring status of the action.
        choices: ['enabled', 'disabled']
        default: 'enabled'
    esc_period:
        description:
            - Default operation step duration. Must be greater than 60 seconds. Accepts seconds, time unit with suffix and user macro
        default: '1h'
    conditions:
        type: list
        description:
            - List of dictionaries of conditions to evaluate.
        suboptions:
            type:
                description: Type (label) of the condition
                choices:
                    # trigger
                    - host_group
                    - host
                    - trigger
                    - trigger_name
                    - trigger_severity
                    - time_period
                    - host_template
                    - application
                    - maintenance_status
                    - event_tag
                    - event_tag_value
                    # discovery
                    - host_IP
                    - discovered_service_type
                    - discovered_service_port
                    - discovery_status
                    - uptime_or_downtime_duration
                    - received_value
                    - discovery_rule
                    - discovery_check
                    - proxy
                    - discovery_object
                    # auto_registration
                    - proxy
                    - host_name
                    - host_metadata
                    # internal
                    - host_group
                    - host
                    - host_template
                    - application
                    - event_type
            value:
                description:
                    - Value to compare with.
            operator:
                description:
                    - Condition operator.
                choices:
                    - '='
                    - '<>'
                    - 'like'
                    - 'not like'
                    - 'in'
                    - '>='
                    - '<='
                    - 'not in'
            formulaid:
                description:
                    - Arbitrary unique ID that is used to reference the condition from a custom expression.
                    - Can only contain capital-case letters.
    formula:
        description:
            - User-defined expression to be used for evaluating conditions of filters with a custom expression.
            - The expression must contain IDs that reference specific filter conditions by its formulaid.
            - The IDs used in the expression must exactly match the ones
              defined in the filter conditions. No condition can remain unused or omitted.
            - Required for custom expression filters.
    operations:
        type: list
        description:
            - List of action operations
        suboptions:
            type:
                description:
                    - Type of operation.
                choices:
                    - send_message
                    - remote_command
                    - add_host
                    - remove_host
                    - add_to_host_group
                    - remove_from_host_group
                    - link_to_template
                    - unlink_from_template
                    - enable_host
                    - disable_host
                    - set_host_inventory_mode
            esc_period:
                description:
                    - Duration of an escalation step in seconds.
                    - Must be greater than 60 seconds.
                    - Accepts seconds, time unit with suffix and user macro.
                    - If set to 0 or 0s, the default action escalation period will be used.
                default: 0s
            esc_step_from:
                description:
                    - Step to start escalation from.
                default: 1
            esc_step_to:
                description:
                    - Step to end escalation at.
                default: 1
            send_to_groups:
                type: list
                description:
                    - User groups to send messages to.
            send_to_users:
                type: list
                description:
                    - Users to send messages to.
            message:
                description:
                    - Operation message text.
            subject:
                description:
                    - Operation message subject.
            media_type:
                description:
                    - Media type that will be used to send the message.
            command_type:
                description:
                    - Type of operation command.
                    - Required when I(type=remote_command).
                choices:
                    - custom_script
                    - ipmi
                    - ssh
                    - telnet
                    - global_script
            command:
                description:
                    - Command to run.
                    - Required when I(type=remote_command) and I(command_type!=global_script).
            execute_on:
                description:
                    - Target on which the custom script operation command will be executed.
                    - Required when I(type=remote_command) and I(command_type=custom_script)
                choices:
                    - agent
                    - server
                    - proxy
            run_on_groups:
                description:
                    - Host groups to run remote commands on
                    - Required when I(type=remote_command) if I(run_on_hosts) is not set
            run_on_hosts:
                description:
                    - Hosts to run remote commands on
                    - Required when I(type=remote_command) if I(run_on_groups) is not set
            ssh_auth_type:
                description:
                    - Authentication method used for SSH commands.
                    - Required when I(type=remote_command) and I(command_type=ssh)
                choices:
                    - password
                    - public_key
            ssh_privatekey_file:
                description:
                    - Name of the private key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh)
            ssh_publickey_file:
                description:
                    - Name of the public key file used for SSH commands with public key authentication.
                    - Required when I(type=remote_command) and I(command_type=ssh)
            username:
                description:
                    - User name used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            password:
                description:
                    - Password used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            port:
                description:
                    - Port number used for authentication.
                    - Required when I(type=remote_command) and I(command_type in [ssh, telnet])
            script_name:
                description:
                    - The name of script used for global script commands.
                    - Required when I(type=remote_command) and I(command_type=global_script)
    recovery_operations:
        type: list
        description:
            - List of recovery operations
            - C(Suboptions) are the same as I(operations)
    acknowledge_operations:
        type: list
        description:
            - List of acknowledge operations
            - C(Suboptions) are the same as I(operations)



extends_documentation_fragment:
    - zabbix

author:
    - Ruben Tsirunyan (@rubentsirunyan)
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''


try:
    from zabbix_api import ZabbixAPI, ZabbixAPISubClass

    # Extend the ZabbixAPI
    # Since the zabbix-api python module too old (version 1.0, no higher version so far),
    # it does not support the 'hostinterface' api calls,
    # so we have to inherit the ZabbixAPI class to add 'hostinterface' support.
    class ZabbixAPIExtends(ZabbixAPI):
        hostinterface = None

        def __init__(self, server, timeout, user, passwd, validate_certs, **kwargs):
            ZabbixAPI.__init__(self, server, timeout=timeout, user=user, passwd=passwd, validate_certs=validate_certs)
            self.hostinterface = ZabbixAPISubClass(self, dict({"prefix": "hostinterface"}, **kwargs))

    HAS_ZABBIX_API = True
except ImportError:
    HAS_ZABBIX_API = False

from ansible.module_utils.basic import AnsibleModule


class Zapi(object):
    def __init__(self, module, zbx):
        self._module = module
        self._zapi = zbx

    def check_if_action_exists(self, name):
        try:
            return self._zapi.action.get({
                "selectOperations": "extend",
                "selectRecoveryOperations": "extend",
                "selectFilter": "extend",
                'selectInventory': 'extend',
                'filter': {'name': [name]}
            })
        except Exception as e:
            self._module.fail_json(msg="Failed to check if action '%s' exists: %s" % (name, e))

    def get_action_by_name(self, name):
        try:
            action_list = self._zapi.action.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [name]}
            })
            if len(action_list) < 1:
                self._module.fail_json(msg="Action not found: " % name)
            else:
                return action_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get ID of '%s': %s" % (name, e))

    # get host by host name
    def get_host_by_host_name(self, host_name):
        try:
            host_list = self._zapi.host.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [host_name]}
            })
            if len(host_list) < 1:
                self._module.fail_json(msg="Host not found: %s" % host_name)
            else:
                return host_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get host '%s': %s" % (host_name, e))

    # get hostgroup by hostgroup name
    def get_hostgroup_by_hostgroup_name(self, hostgroup_name):
        try:
            hostgroup_list = self._zapi.hostgroup.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [hostgroup_name]}
            })
            if len(hostgroup_list) < 1:
                self._module.fail_json(msg="Host group not found: %s" % hostgroup_name)
            else:
                return hostgroup_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get host group '%s': %s" % (host_group, e))

    # get template by template name
    def get_template_by_template_name(self, template_name):
        try:
            template_list = self._zapi.template.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [template_name]}
            })
            if len(template_list) < 1:
                self._module.fail_json(msg="Template not found: %s" % template_name)
            else:
                return template_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get template '%s': %s" % (template_name, e))

    def get_trigger_by_trigger_name(self, trigger_name):
        try:
            trigger_list = self._zapi.trigger.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'description': [trigger_name]}
            })
            if len(trigger_list) < 1:
                self._module.fail_json(msg="Trigger not found: %s" % trigger_name)
            else:
                return trigger_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get trigger '%s': %s" % (trigger_name, e))

    def get_discovery_rule_by_discovery_rule_name(self, discovery_rule_name):
        try:
            discovery_rule_list = self._zapi.drule.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [discovery_rule_name]}
            })
            if len(discovery_rule_list) < 1:
                self._module.fail_json(msg="Discovery rule not found: %s" % discovery_rule_name)
            else:
                return discovery_rule_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get discovery rule '%s': %s" % (discovery_rule_name, e))

    def get_discovery_check_by_discovery_check_name(self, discovery_check_name):
        try:
            discovery_check_list = self._zapi.dcheck.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [discovery_check_name]}
            })
            if len(discovery_check_list) < 1:
                self._module.fail_json(msg="Discovery check not found: %s" % discovery_check_name)
            else:
                return discovery_check_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get discovery check '%s': %s" % (discovery_check_name, e))

    def get_proxy_by_proxy_name(self, proxy_name):
        try:
            proxy_list = self._zapi.proxy.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'host': [proxy_name]}
            })
            if len(proxy_list) < 1:
                self._module.fail_json(msg="Proxy not found: %s" % proxy_name)
            else:
                return proxy_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get proxy '%s': %s" % (proxy_name, e))

    # get mediatype by mediatype name
    def get_mediatype_by_mediatype_name(self, mediatype_name):
        try:
            mediatype_list = self._zapi.mediatype.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'description': [mediatype_name]}
            })
            if len(mediatype_list) < 1:
                self._module.fail_json(msg="Media type not found: %s" % mediatype_name)
            else:
                return mediatype_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get mediatype '%s': %s" % (mediatype_name, e))

    # get user by user name
    def get_user_by_user_name(self, user_name):
        try:
            user_list = self._zapi.user.get({
                'output': 'extend',
                'selectInventory':
                'extend', 'filter': {'alias': [user_name]}
            })
            if len(user_list) < 1:
                self._module.fail_json(msg="User not found: %s" % user_name)
            else:
                return user_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get user '%s': %s" % (user_name, e))

    # get usergroup by usergroup name
    def get_usergroup_by_usergroup_name(self, usergroup_name):
        try:
            usergroup_list = self._zapi.usergroup.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [usergroup_name]}
            })
            if len(usergroup_list) < 1:
                self._module.fail_json(msg="User group not found: %s" % usergroup_name)
            else:
                return usergroup_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get user group '%s': %s" % (usergroup_name, e))

    # get script by script name
    def get_script_by_script_name(self, script_name):
        try:
            if script_name is None:
                return {}
            script_list = self._zapi.script.get({
                'output': 'extend',
                'selectInventory': 'extend',
                'filter': {'name': [script_name]}
            })
            if len(script_list) < 1:
                self._module.fail_json(msg="Script not found: %s" % script_name)
            else:
                return script_list[0]
        except Exception as e:
            self._module.fail_json(msg="Failed to get script '%s': %s" % (script_name, e))


class Action(object):
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_parameters(self, **kwargs):
        return {
            'name': kwargs['name'],
            'eventsource': map_to_int([
                'trigger',
                'discovery',
                'auto_registration',
                'internal'], kwargs['event_source']),
            'esc_period': kwargs.get('esc_period'),
            'filter': kwargs['conditions'],
            'operations': kwargs['operations'],
            'recovery_operations': kwargs.get('recovery_operations'),
            'acknowledge_operations': kwargs.get('acknowledge_operations'),
            'status': map_to_int([
                'enabled',
                'disabled'], kwargs['status'])
        }

    def check_difference(self, **kwargs):
        existing_action = convert_unicode_to_str(self._zapi_wrapper.check_if_action_exists(kwargs['name'])[0])
        parameters = convert_unicode_to_str(self._construct_parameters(**kwargs))
        change_parameters = {}
        return cleanup_data(compare_dictionaries(parameters, existing_action, change_parameters))

    def update_action(self, **kwargs):
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be updated if check mode was not specified: %s" % kwargs, changed=True)
            kwargs['actionid'] = kwargs.pop('action_id')
            return self._zapi.action.update(kwargs)
        except Exception as e:
            self._module.fail_json(msg="Failed to update action '%s': %s" % (kwargs['actionid'], e))

    def add_action(self, **kwargs):
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be added if check mode was not specified", changed=True)
            parameters = self._construct_parameters(**kwargs)
            action_list = self._zapi.action.create(parameters)
            return action_list['actionids'][0]
        except Exception as e:
            self._module.fail_json(msg="Failed to create action '%s': %s" % (kwargs['name'], e))

    def delete_action(self, action_id):
        try:
            if self._module.check_mode:
                self._module.exit_json(msg="Action would be deleted if check mode was not specified", changed=True)
            return self._zapi.action.delete([action_id])
        except Exception as e:
            self._module.fail_json(msg="Failed to delete action '%s': %s" % (action_id, e))


class Operations(object):
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        # self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_opmessage(self, operation):
        return {
            'default_msg': '0' if 'message' in operation or 'subject' in operation else '1',
            'mediatypeid': self._zapi_wrapper.get_mediatype_by_mediatype_name(
                operation.get('media_type')
            )['mediatypeid'] if operation.get('media_type') is not None else None,
            'message': operation.get('message'),
            'subject': operation.get('subject'),
        }

    def _construct_opmessage_usr(self, operation):
        if operation.get('send_to_users') is None:
            return None
        return [{
            'userid': self._zapi_wrapper.get_user_by_user_name(_user)['userid']
        } for _user in operation.get('send_to_users')]

    def _construct_opmessage_grp(self, operation):
        if operation.get('send_to_groups') is None:
            return None
        return [{
            'usrgripid': self._zapi_wrapper.get_usergroup_by_usergroup_name(_group)['usrgripid']
        } for _group in operation.get('send_to_groups')]

    def _construct_operationtype(self, operation):
        return map_to_int([
            "send_message",
            "remote_command",
            "add_host",
            "remove_host",
            "add_to_host_group",
            "remove_from_host_group",
            "link_to_template",
            "unlink_from_template",
            "enable_host",
            "disable_host",
            "set_host_inventory_mode"], operation['type']
        )

    def _construct_opcommand(self, operation):
        return {
            'type': map_to_int([
                'custom_script',
                'ipmi',
                'ssh',
                'telnet',
                'global_script'], operation.get('command_type', 'custom_script')),
            'command': operation.get('command'),
            'execute_on': map_to_int([
                'agent',
                'server',
                'proxy'], operation.get('execute_on', 'server')),
            'scriptid': self._zapi_wrapper.get_script_by_script_name(
                operation.get('script_name')
            ).get('scriptid'),
            'authtype': map_to_int([
                'password',
                'private_key'
            ], operation.get('ssh_auth_type', 'password')),
            'privatekey': operation.get('ssh_privatekey_file'),
            'publickey': operation.get('ssh_publickey_file'),
            'username': operation.get('username'),
            'password': operation.get('password'),
            'port': operation.get('port')
        }

    def _construct_opcommand_hst(self, operation):
        if operation.get('run_on_host') is None:
            return None
        return [{
            'hostid': self._zapi_wrapper.get_host_by_host_name(_host)['hostid']
        } if _host != '0' else {'hostid': '0'} for _host in operation.get('run_on_host')]

    def _construct_opcommand_grp(self, operation):
        if operation.get('run_on_group') is None:
            return None
        return [{
            'hostid': self._zapi_wrapper.get_host_by_host_name(_host)['hostid']
        } if _host != '0' else {'hostid': '0'} for _host in operation.get('run_on_group')]

    def _construct_opgroup(self, operation):
        return [{
            'groupid': self._zapi_wrapper.get_hostgroup_by_hostgroup_name(_group)['groupid']
        } for _group in operation.get('host_groups', [])]

    def _construct_optemplate(self, operation):
        return [{
            'templateid': self._zapi_wrapper.get_template_by_template_name(_template)['templateid']
        } for _template in operation.get('templates', [])]

    def _construct_opinventory(self, operation):
        return {'inventory_mode': operation.get('inventory')}

    def construct_the_data(self, operations):
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
                'esc_period': op.get('esc_period'),
                'esc_step_from': op.get('esc_step_from'),
                'esc_step_to': op.get('esc_step_to')
            }
            # Send Message type
            if constructed_operation['operationtype'] == '0':
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)

            # Add to/Remove from host group
            if constructed_operation['operationtype'] in ('4', '5'):
                constructed_operation['opgroup'] = self._construct_opgroup(op)

            # Link/Unlink template
            if constructed_operation['operationtype'] in ('6', '7'):
                constructed_operation['optemplate'] = self._construct_optemplate(op)

            # Set inventory mode
            if constructed_operation['operationtype'] == '10':
                constructed_operation['opinventory'] = self._construct_opinventory(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class RecoveryOperations(Operations):
    def _construct_operationtype(self, operation):
        return map_to_int([
            "send_message",
            "remote_command",
            "placeholder1",
            "placeholder2",
            "placeholder3",
            "placeholder4",
            "placeholder5",
            "placeholder6",
            "placeholder7",
            "placeholder8",
            "placeholder9",
            "notify_all_involved"], operation['type']
        )

    def construct_the_data(self, operations):
        if operations is None:
            return None
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
            }

            # Send Message type
            if constructed_operation['operationtype'] in ('0', '11'):
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class AcknowledgeOperations(Operations):
    def _construct_operationtype(self, operation):
        return map_to_int([
            "send_message",
            "remote_command",
            "placeholder1",
            "placeholder2",
            "placeholder3",
            "placeholder4",
            "placeholder5",
            "placeholder6",
            "placeholder7",
            "placeholder8",
            "placeholder9",
            "placeholder10",
            "notify_all_involved"], operation['type']
        )

    def construct_the_data(self, operations):
        if operations is None:
            return None
        constructed_data = []
        for op in operations:
            operation_type = self._construct_operationtype(op)
            constructed_operation = {
                'operationtype': operation_type,
            }

            # Send Message type
            if constructed_operation['operationtype'] in ('0', '11'):
                constructed_operation['opmessage'] = self._construct_opmessage(op)
                constructed_operation['opmessage_usr'] = self._construct_opmessage_usr(op)
                constructed_operation['opmessage_grp'] = self._construct_opmessage_grp(op)

            # Send Command type
            if constructed_operation['operationtype'] == '1':
                constructed_operation['opcommand'] = self._construct_opcommand(op)
                constructed_operation['opcommand_hst'] = self._construct_opcommand_hst(op)
                constructed_operation['opcommand_grp'] = self._construct_opcommand_grp(op)

            constructed_data.append(constructed_operation)

        return cleanup_data(constructed_data)


class Filter(object):
    def __init__(self, module, zbx, zapi_wrapper):
        self._module = module
        self._zapi = zbx
        self._zapi_wrapper = zapi_wrapper

    def _construct_evaltype(self, _eval):
        return {
            'evaltype': '3',
            'formula': _eval
        }

    def _construct_conditiontype(self, _condition):
        return map_to_int([
            "host_group",
            "host",
            "trigger",
            "trigger_name",
            "trigger_severity",
            "trigger_value",
            "time_period",
            "host_ip",
            "discovered_service_type",
            "discovered_service_port",
            "discovery_status",
            "uptime_or_downtime_duration",
            "received_value",
            "host_template",
            "zabbix_has_no_value_for_14",
            "application",
            "maintenance_status",
            "zabbix_has_no_value_for_17",
            "discovery_rule",
            "discovery_check",
            "proxy",
            "discovery_object",
            "host_name",
            "event_type",
            "host_metadata",
            "event_tag",
            "event_tag_value"], _condition['type']
        )

    def _construct_operator(self, _condition):
        return map_to_int([
            "=",
            "<>",
            "like",
            "not like",
            "in",
            ">=",
            "<=",
            "not in"], _condition['operator']
        )

    def _construct_value(self, conditiontype, value):
        # Host group
        if conditiontype == '0':
            return self._zapi_wrapper.get_hostgroup_by_hostgroup_name(value)['groupid']
        # Host
        if conditiontype == '1':
            return self._zapi_wrapper.get_host_by_host_name(value)['hostid']
        # Trigger
        if conditiontype == '2':
            return self._zapi_wrapper.get_trigger_by_trigger_name(value)['triggerid']
        # Trigger name: return as is
        # Trigger severity
        if conditiontype == '4':
            return map_to_int([
                "not classified",
                "information",
                "warning",
                "average",
                "high",
                "disaster"], value or "not classified"
            )

        # Trigger value
        if conditiontype == '5':
            return map_to_int([
                "ok",
                "problem"], value or "ok"
            )
        # Time period: return as is
        # Host IP: return as is
        # Discovered service type
        if conditiontype == '8':
            return map_to_int([
                "SSH",
                "LDAP",
                "SMTP",
                "FTP",
                "HTTP",
                "POP",
                "NNTP",
                "IMAP",
                "TCP",
                "Zabbix agent",
                "SNMPv1 agent",
                "SNMPv2 agent",
                "ICMP ping",
                "SNMPv3 agent",
                "HTTPS",
                "Telnet"], value
            )
        # Discovered service port: return as is
        # Discovery status
        if conditiontype == '10':
            return map_to_int([
                "up",
                "down",
                "discovered",
                "lost"], value
            )
        if conditiontype == '13':
            return self._zapi_wrapper.get_template_by_template_name(value)['templateid']
        if conditiontype == '18':
            return self._zapi_wrapper.get_discovery_rule_by_discovery_rule_name(value)['druleid']
        if conditiontype == '19':
            return self._zapi_wrapper.get_discovery_check_by_discovery_check_name(value)['dcheckid']
        if conditiontype == '20':
            return self._zapi_wrapper.get_proxy_by_proxy_name(value)['proxyid']
        if conditiontype == '21':
            return map_to_int([
                "pchldrfor0",
                "host",
                "service"], value
            )
        if conditiontype == '23':
            return map_to_int([
                "item in not supported state",
                "item in normal state",
                "LLD rule in not supported state",
                "LLD rule in normal state",
                "trigger in unknown state",
                "trigger in normal state"], value
            )
        return value

    def construct_the_data(self, _formula, _conditions):
        if _conditions is None:
            return None
        constructed_data = {}
        constructed_data['evaltype'] = self._construct_evaltype(_formula)['evaltype']
        constructed_data['formula'] = self._construct_evaltype(_formula)['formula']
        constructed_data['conditions'] = []
        for cond in _conditions:
            condition_type = self._construct_conditiontype(cond)
            constructed_data['conditions'].append({
                "conditiontype": condition_type,
                "value": self._construct_value(condition_type, cond.get("value")),
                "value2": cond.get("value2"),
                "formulaid": cond.get("formulaid"),
                "operator": self._construct_operator(cond)
            })
        return cleanup_data(constructed_data)


def convert_unicode_to_str(data):
    if isinstance(data, (str, unicode)):
        return str(data)
    elif isinstance(data, dict):
        return dict(map(convert_unicode_to_str, data.items()))
    elif isinstance(data, (list, tuple, set)):
        return type(data)(map(convert_unicode_to_str, data))


def map_to_int(strs, value):
    """ Convert string values to integers"""
    tmp_dict = dict(zip(strs, list(range(len(strs)))))
    return str(tmp_dict[value])


def compare_lists(l1, l2, diff_dict):
    if len(l1) != len(l2):
        diff_dict.append(l1)
        return diff_dict
    for i, item in enumerate(l1):
        if isinstance(item, dict):
            diff_dict.insert(i, {})
            diff_dict[i] = compare_dictionaries(item, l2[i], diff_dict[i])
        else:
            if item != l2[i]:
                diff_dict.append(item)
    while {} in diff_dict:
        diff_dict.remove({})
    return diff_dict


def compare_dictionaries(d1, d2, diff_dict):
    for k, v in d1.items():
        if k not in d2:
            diff_dict[k] = v
            continue
        if isinstance(v, dict):
            diff_dict[k] = {}
            compare_dictionaries(v, d2[k], diff_dict[k])
            if diff_dict[k] == {}:
                del diff_dict[k]
            else:
                diff_dict[k] = v
        elif isinstance(v, list):
            diff_dict[k] = []
            compare_lists(v, d2[k], diff_dict[k])
            if diff_dict[k] == []:
                del diff_dict[k]
            else:
                diff_dict[k] = v
        else:
            if v != d2[k]:
                diff_dict[k] = v
    return diff_dict


def cleanup_data(obj):
    if isinstance(obj, (list, tuple, set)):
        return type(obj)(cleanup_data(x) for x in obj if x is not None)
    elif isinstance(obj, dict):
        return type(obj)((cleanup_data(k), cleanup_data(v))
                         for k, v in obj.items() if k is not None and v is not None)
    else:
        return obj


def main():
    module = AnsibleModule(
        argument_spec=dict(
            server_url=dict(type='str', required=True, aliases=['url']),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            http_login_user=dict(type='str', required=False, default=None),
            http_login_password=dict(type='str', required=False, default=None, no_log=True),
            validate_certs=dict(type='bool', required=False, default=True),
            esc_period=dict(type='str', required=False, default='1h'),
            timeout=dict(type='int', default=10),
            name=dict(type='str', required=True),
            event_source=dict(type='str', required=True, choices=['trigger', 'discovery', 'auto_registration', 'internal']),
            state=dict(type='str', required=False, default='present', choices=['present', 'absent']),
            status=dict(type='str', required=False, default='enabled', choices=['enabled', 'disabled']),
            conditions=dict(type='list', required=False, default=None),
            formula=dict(type='str', required=False, default=None),
            operations=dict(type='list', required=False, default=None),
            recovery_operations=dict(type='list', required=False, default=None),
            acknowledge_operations=dict(type='list', required=False, default=None)
        ),
        supports_check_mode=True
    )

    if not HAS_ZABBIX_API:
        module.fail_json(msg="Missing required zabbix-api module (check docs or install with: pip install zabbix-api)")

    server_url = module.params['server_url']
    login_user = module.params['login_user']
    login_password = module.params['login_password']
    http_login_user = module.params['http_login_user']
    http_login_password = module.params['http_login_password']
    validate_certs = module.params['validate_certs']
    timeout = module.params['timeout']
    name = module.params['name']
    esc_period = module.params['esc_period']
    event_source = module.params['event_source']
    state = module.params['state']
    status = module.params['status']
    conditions = module.params['conditions']
    formula = module.params['formula']
    operations = module.params['operations']
    recovery_operations = module.params['recovery_operations']
    acknowledge_operations = module.params['acknowledge_operations']

    try:
        zbx = ZabbixAPIExtends(server_url, timeout=timeout, user=http_login_user, passwd=http_login_password,
                               validate_certs=validate_certs)
        zbx.login(login_user, login_password)
    except Exception as e:
        module.fail_json(msg="Failed to connect to Zabbix server: %s" % e)

    zapi_wrapper = Zapi(module, zbx)

    action = Action(module, zbx, zapi_wrapper)

    action_exists = zapi_wrapper.check_if_action_exists(name)
    ops = Operations(module, zbx, zapi_wrapper)
    recovery_ops = RecoveryOperations(module, zbx, zapi_wrapper)
    acknowledge_ops = AcknowledgeOperations(module, zbx, zapi_wrapper)

    fltr = Filter(module, zbx, zapi_wrapper)

    if action_exists:
        action_id = zapi_wrapper.get_action_by_name(name)['actionid']
        if state == "absent":
            result = action.delete_action(action_id)
            module.exit_json(changed=True, result="Action Deleted: %s, ID: %s" % (name, result))
        else:
            difference = action.check_difference(
                action_id=action_id,
                name=name,
                event_source=event_source,
                esc_period=esc_period,
                status=status,
                operations=ops.construct_the_data(operations),
                recovery_operations=recovery_ops.construct_the_data(recovery_operations),
                acknowledge_operations=acknowledge_ops.construct_the_data(acknowledge_operations),
                conditions=fltr.construct_the_data(formula, conditions)
            )

            if difference == {}:
                module.exit_json(changed=False, result="Action is up to date: %s" % (name))
            else:
                result = action.update_action(
                    action_id=action_id,
                    **difference
                )
                module.exit_json(changed=True, result="Action Updated: %s, ID: %s" % (name, result))
    else:
        if state == "absent":
            module.exit_json(changed=False)
        else:
            action_id = action.add_action(
                name=name,
                event_source=event_source,
                esc_period=esc_period,
                status=status,
                operations=ops.construct_the_data(operations),
                recovery_operations=recovery_ops.construct_the_data(recovery_operations),
                acknowledge_operations=acknowledge_ops.construct_the_data(acknowledge_operations),
                conditions=fltr.construct_the_data(formula, conditions)
            )
            module.exit_json(changed=True, result="Action created: %s, ID: %s" % (name, action_id))


if __name__ == '__main__':
    main()
