#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Ansible module to manage CheckPoint Firewall (c) 2019
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
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: cp_mgmt_simple_gateway
short_description: Manages simple-gateway objects on Checkpoint over Web Services API
description:
  - Manages simple-gateway objects on Checkpoint devices including creating, updating and removing objects.
    All operations are performed over Web Services API.
version_added: "2.9"
author: "Or Soffer (@chkp-orso)"
options:
  name:
    description:
      - Object name.
    type: str
    required: True
  ip_address:
    description:
      - IPv4 or IPv6 address. If both addresses are required use ipv4-address and ipv6-address fields explicitly.
    type: str
  ipv4_address:
    description:
      - IPv4 address.
    type: str
  ipv6_address:
    description:
      - IPv6 address.
    type: str
  anti_bot:
    description:
      - Anti-Bot blade enabled.
    type: bool
  anti_virus:
    description:
      - Anti-Virus blade enabled.
    type: bool
  application_control:
    description:
      - Application Control blade enabled.
    type: bool
  content_awareness:
    description:
      - Content Awareness blade enabled.
    type: bool
  firewall:
    description:
      - Firewall blade enabled.
    type: bool
  firewall_settings:
    description:
      - N/A
    type: list
    suboptions:
      auto_calculate_connections_hash_table_size_and_memory_pool:
        description:
          - N/A
        type: bool
      auto_maximum_limit_for_concurrent_connections:
        description:
          - N/A
        type: bool
      connections_hash_size:
        description:
          - N/A
        type: int
      maximum_limit_for_concurrent_connections:
        description:
          - N/A
        type: int
      maximum_memory_pool_size:
        description:
          - N/A
        type: int
      memory_pool_size:
        description:
          - N/A
        type: int
  interfaces:
    description:
      - Network interfaces. When a gateway is updated with a new interfaces, the existing interfaces are removed.
    type: list
  ips:
    description:
      - Intrusion Prevention System blade enabled.
    type: bool
  logs_settings:
    description:
      - N/A
    type: list
    suboptions:
      alert_when_free_disk_space_below:
        description:
          - N/A
        type: bool
      alert_when_free_disk_space_below_threshold:
        description:
          - N/A
        type: int
      alert_when_free_disk_space_below_type:
        description:
          - N/A
        type: str
        choices: ['none', 'log', 'popup alert', 'mail alert', 'snmp trap alert',
                 'user defined alert no.1', 'user defined alert no.2', 'user defined alert no.3']
      before_delete_keep_logs_from_the_last_days:
        description:
          - N/A
        type: bool
      before_delete_keep_logs_from_the_last_days_threshold:
        description:
          - N/A
        type: int
      before_delete_run_script:
        description:
          - N/A
        type: bool
      before_delete_run_script_command:
        description:
          - N/A
        type: str
      delete_index_files_older_than_days:
        description:
          - N/A
        type: bool
      delete_index_files_older_than_days_threshold:
        description:
          - N/A
        type: int
      delete_index_files_when_index_size_above:
        description:
          - N/A
        type: bool
      delete_index_files_when_index_size_above_threshold:
        description:
          - N/A
        type: int
      delete_when_free_disk_space_below:
        description:
          - N/A
        type: bool
      delete_when_free_disk_space_below_threshold:
        description:
          - N/A
        type: int
      detect_new_citrix_ica_application_names:
        description:
          - N/A
        type: bool
      forward_logs_to_log_server:
        description:
          - N/A
        type: bool
      forward_logs_to_log_server_name:
        description:
          - N/A
        type: str
      forward_logs_to_log_server_schedule_name:
        description:
          - N/A
        type: str
      free_disk_space_metrics:
        description:
          - N/A
        type: str
        choices: ['mbytes', 'percent']
      perform_log_rotate_before_log_forwarding:
        description:
          - N/A
        type: bool
      reject_connections_when_free_disk_space_below_threshold:
        description:
          - N/A
        type: bool
      reserve_for_packet_capture_metrics:
        description:
          - N/A
        type: str
        choices: ['percent', 'mbytes']
      reserve_for_packet_capture_threshold:
        description:
          - N/A
        type: int
      rotate_log_by_file_size:
        description:
          - N/A
        type: bool
      rotate_log_file_size_threshold:
        description:
          - N/A
        type: int
      rotate_log_on_schedule:
        description:
          - N/A
        type: bool
      rotate_log_schedule_name:
        description:
          - N/A
        type: str
      stop_logging_when_free_disk_space_below:
        description:
          - N/A
        type: bool
      stop_logging_when_free_disk_space_below_threshold:
        description:
          - N/A
        type: int
      turn_on_qos_logging:
        description:
          - N/A
        type: bool
      update_account_log_every:
        description:
          - N/A
        type: int
  one_time_password:
    description:
      - N/A
    type: str
  os_name:
    description:
      - Gateway platform operating system.
    type: str
  save_logs_locally:
    description:
      - Save logs locally on the gateway.
    type: bool
  send_alerts_to_server:
    description:
      - Server(s) to send alerts to.
    type: list
  send_logs_to_backup_server:
    description:
      - Backup server(s) to send logs to.
    type: list
  send_logs_to_server:
    description:
      - Server(s) to send logs to.
    type: list
  tags:
    description:
      - Collection of tag identifiers.
    type: list
  threat_emulation:
    description:
      - Threat Emulation blade enabled.
    type: bool
  threat_extraction:
    description:
      - Threat Extraction blade enabled.
    type: bool
  url_filtering:
    description:
      - URL Filtering blade enabled.
    type: bool
  version:
    description:
      - Gateway platform version.
    type: str
  vpn:
    description:
      - VPN blade enabled.
    type: bool
  vpn_settings:
    description:
      - Gateway VPN settings.
    type: list
    suboptions:
      maximum_concurrent_ike_negotiations:
        description:
          - N/A
        type: int
      maximum_concurrent_tunnels:
        description:
          - N/A
        type: int
  color:
    description:
      - Color of the object. Should be one of existing colors.
    type: str
    choices: ['aquamarine', 'black', 'blue', 'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki',
             'orchid', 'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick', 'brown',
             'forest green', 'gold', 'dark gold', 'gray', 'dark gray', 'light green', 'lemon chiffon', 'coral',
             'sea green', 'sky blue', 'magenta', 'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange',
             'red', 'sienna', 'yellow']
  comments:
    description:
      - Comments string.
    type: str
  details_level:
    description:
      - The level of detail for some of the fields in the response can vary from showing only the UID value of
        the object to a fully detailed representation of the object.
    type: str
    choices: ['uid', 'standard', 'full']
  groups:
    description:
      - Collection of group identifiers.
    type: list
  ignore_warnings:
    description:
      - Apply changes ignoring warnings.
    type: bool
  ignore_errors:
    description:
      - Apply changes ignoring errors. You won't be able to publish such a changes. If ignore-warnings flag was
        omitted - warnings will also be ignored.
    type: bool
extends_documentation_fragment: checkpoint_objects
"""

EXAMPLES = """
- name: add-simple-gateway
  cp_mgmt_simple_gateway:
    anti_bot: true
    anti_virus: true
    application_control: true
    color: yellow
    firewall: true
    interfaces:
    _ anti_spoofing: true
      ipv4_address: 192.0.2.230
      ipv4_network_mask: 255.255.255.128
      name: eth0
      topology: EXTERNAL
    _ anti_spoofing: true
      ipv4_address: 192.0.2.88
      ipv4_network_mask: 255.255.255.0
      name: eth1
      topology: INTERNAL
    ips: true
    ipv4_address: 192.0.2.230
    name: gw1
    one_time_password: aaaa
    threat_emulation: true
    url_filtering: true
    version: R80
    vpn: true

- name: set-simple-gateway
  cp_mgmt_simple_gateway:
    anti_bot: true
    anti_virus: true
    application_control: true
    ips: true
    name: test_gateway
    threat_emulation: true
    url_filtering: true
    vpn: true

- name: delete-simple-gateway
  cp_mgmt_simple_gateway:
    name: gw1
    state: absent
"""

RETURN = """
cp_mgmt_simple_gateway:
  description: The checkpoint object created or updated.
  returned: always, except when deleting the object.
  type: dict
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.checkpoint.checkpoint import checkpoint_argument_spec_for_objects, api_call


def main():
    argument_spec = dict(
        name=dict(type='str', required=True),
        ip_address=dict(type='str'),
        ipv4_address=dict(type='str'),
        ipv6_address=dict(type='str'),
        anti_bot=dict(type='bool'),
        anti_virus=dict(type='bool'),
        application_control=dict(type='bool'),
        content_awareness=dict(type='bool'),
        firewall=dict(type='bool'),
        firewall_settings=dict(type='list', options=dict(
            auto_calculate_connections_hash_table_size_and_memory_pool=dict(type='bool'),
            auto_maximum_limit_for_concurrent_connections=dict(type='bool'),
            connections_hash_size=dict(type='int'),
            maximum_limit_for_concurrent_connections=dict(type='int'),
            maximum_memory_pool_size=dict(type='int'),
            memory_pool_size=dict(type='int')
        )),
        interfaces=dict(type='list'),
        ips=dict(type='bool'),
        logs_settings=dict(type='list', options=dict(
            alert_when_free_disk_space_below=dict(type='bool'),
            alert_when_free_disk_space_below_threshold=dict(type='int'),
            alert_when_free_disk_space_below_
                                                                           type=dict(type='str', choices=['none', 'log',
                                                                            'popup alert', 'mail alert',
                                                                            'snmp trap alert',
                                                                            'user defined alert no.1',
                                                                            'user defined alert no.2',
                                                                            'user defined alert no.3']),
            before_delete_keep_logs_from_the_last_days=dict(type='bool'),
            before_delete_keep_logs_from_the_last_days_threshold=dict(type='int'),
            before_delete_run_script=dict(type='bool'),
            before_delete_run_script_command=dict(type='str'),
            delete_index_files_older_than_days=dict(type='bool'),
            delete_index_files_older_than_days_threshold=dict(type='int'),
            delete_index_files_when_index_size_above=dict(type='bool'),
            delete_index_files_when_index_size_above_threshold=dict(type='int'),
            delete_when_free_disk_space_below=dict(type='bool'),
            delete_when_free_disk_space_below_threshold=dict(type='int'),
            detect_new_citrix_ica_application_names=dict(type='bool'),
            forward_logs_to_log_server=dict(type='bool'),
            forward_logs_to_log_server_name=dict(type='str'),
            forward_logs_to_log_server_schedule_name=dict(type='str'),
            free_disk_space_metrics=dict(type='str', choices=['mbytes', 'percent']),
            perform_log_rotate_before_log_forwarding=dict(type='bool'),
            reject_connections_when_free_disk_space_below_threshold=dict(type='bool'),
            reserve_for_packet_capture_metrics=dict(type='str', choices=['percent', 'mbytes']),
            reserve_for_packet_capture_threshold=dict(type='int'),
            rotate_log_by_file_size=dict(type='bool'),
            rotate_log_file_size_threshold=dict(type='int'),
            rotate_log_on_schedule=dict(type='bool'),
            rotate_log_schedule_name=dict(type='str'),
            stop_logging_when_free_disk_space_below=dict(type='bool'),
            stop_logging_when_free_disk_space_below_threshold=dict(type='int'),
            turn_on_qos_logging=dict(type='bool'),
            update_account_log_every=dict(type='int')
        )),
        one_time_password=dict(type='str'),
        os_name=dict(type='str'),
        save_logs_locally=dict(type='bool'),
        send_alerts_to_server=dict(type='list'),
        send_logs_to_backup_server=dict(type='list'),
        send_logs_to_server=dict(type='list'),
        tags=dict(type='list'),
        threat_emulation=dict(type='bool'),
        threat_extraction=dict(type='bool'),
        url_filtering=dict(type='bool'),
        version=dict(type='str'),
        vpn=dict(type='bool'),
        vpn_settings=dict(type='list', options=dict(
            maximum_concurrent_ike_negotiations=dict(type='int'),
            maximum_concurrent_tunnels=dict(type='int')
        )),
        color=dict(type='str', choices=['aquamarine', 'black', 'blue',
                                        'crete blue', 'burlywood', 'cyan', 'dark green', 'khaki', 'orchid',
                                        'dark orange', 'dark sea green', 'pink', 'turquoise', 'dark blue', 'firebrick',
                                        'brown', 'forest green', 'gold', 'dark gold', 'gray', 'dark gray',
                                        'light green', 'lemon chiffon', 'coral', 'sea green', 'sky blue', 'magenta',
                                        'purple', 'slate blue', 'violet red', 'navy blue', 'olive', 'orange', 'red',
                                        'sienna', 'yellow']),
        comments=dict(type='str'),
        details_level=dict(type='str', choices=['uid', 'standard', 'full']),
        groups=dict(type='list'),
        ignore_warnings=dict(type='bool'),
        ignore_errors=dict(type='bool')
    )
    argument_spec.update(checkpoint_argument_spec_for_objects)

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    api_call_object = 'simple-gateway'

    result = api_call(module, api_call_object)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
