#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#############################################
#                WARNING                    #
#############################################
#
# This file is auto generated by the resource
#   module builder playbook.
#
# Do not edit this file manually.
#
# Changes to this file will be over written
#   by the resource module builder.
#
# Changes should be made in the model used to
#   generate this file or in the resource module
#   builder template.
#
#############################################

"""
The module file for iosxr_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
  module: iosxr_interfaces
  version_added: 2.9
  short_description: Manage interface attributes on Cisco IOS-XR network devices
  description: This module manages the interface attributes on Cisco IOS-XR network devices.
  author: Sumit Jaiswal (@justjais)
  notes:
  - Tested against Cisco IOS-XRv Version 6.1.3 on VIRL.
  - This module works with connection C(network_cli).
  options:
    config:
      description: A dictionary of interface options
      type: list
      elements: dict
      suboptions:
        name:
          description:
          - Full name of the interface to configure in C(type + path) format. e.g. C(GigabitEthernet0/0/0/0)
          type: str
          required: True
        description:
          description:
          - Interface description.
          type: str
        enabled:
          default: True
          description:
          - Administrative state of the interface.
          - Set the value to C(True) to administratively enable the interface or C(False) to disable it.
          type: bool
        speed:
          description:
          - Configure the speed for an interface. Default is auto-negotiation when not configured.
          type: int
          choices: [10, 100, 1000]
        mtu:
          description:
          - Sets the MTU value for the interface. Applicable for Ethernet interfaces only.
          - Refer to vendor documentation for valid values.
          type: int
        duplex:
          description:
          - Configures the interface duplex mode. Default is auto-negotiation when not configured.
          type: str
          choices: ['full', 'half']
    state:
      choices:
      - merged
      - replaced
      - overridden
      - deleted
      default: merged
      description:
      - The state the configuration should be left in
      type: str
"""

EXAMPLES = """
---
# Using merged

# Before state:
# -------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Replaced by Ansible Team
#  mtu 2000
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  dot1q native vlan 1021
# !

- name: Configure Ethernet interfaces
  iosxr_interfaces:
    config:
      - name: GigabitEthernet0/0/0/2
        description: 'Configured by Ansible'
        enabled: True
      - name: GigabitEthernet0/0/0/3
        description: 'Configured by Ansible Network'
        enabled: False
        duplex: full
    state: merged

# After state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Configured and Merged by Ansible Network
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Configured and Merged by Ansible Network
#  mtu 2600
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  duplex full
#  shutdown
#  dot1q native vlan 1021
# !

# Using replaced

# Before state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  description Configured by Ansible
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Test
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  dot1q native vlan 1021
# !

- name: Configure following interfaces and replace their existing config
  iosxr_interfaces:
    config:
      - name: GigabitEthernet0/0/0/2
        description: Configured by Ansible
        enabled: True
        mtu: 2000
      - name: GigabitEthernet0/0/0/3
        description: 'Configured by Ansible Network'
        enabled: False
        duplex: auto
    state: replaced

# After state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  description Configured by Ansible
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Configured and Replaced by Ansible
#  mtu 2000
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Configured and Replaced by Ansible Network
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  duplex half
#  shutdown
#  dot1q native vlan 1021
# !

# Using overridden

# Before state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Configured by Ansible
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Configured by Ansible
#  mtu 2600
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  duplex full
#  shutdown
#  dot1q native vlan 1021
# !

- name: Override interfaces
  iosxr_interfaces:
    config:
      - name: GigabitEthernet0/0/0/2
        description: 'Configured by Ansible'
        enabled: True
        duplex: auto
      - name: GigabitEthernet0/0/0/3
        description: 'Configured by Ansible Network'
        enabled: False
        speed: 1000
    state: overridden

# After state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Configured and Overridden by Ansible Network
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  speed 1000
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Configured and Overridden by Ansible Network
#  mtu 2000
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  duplex full
#  shutdown
#  dot1q native vlan 1021
# !

# Using deleted

# Before state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  description Configured and Overridden by Ansible Network
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  speed 1000
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  description Configured and Overridden by Ansible Network
#  mtu 2000
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  duplex full
#  shutdown
#  dot1q native vlan 1021
# !

- name: Delete IOSXR interfaces as in given arguments
  iosxr_interfaces:
    config:
      - name: GigabitEthernet0/0/0/2
      - name: GigabitEthernet0/0/0/3
    state: deleted

# After state:
# ------------
#
# viosxr#show running-config interface
# interface GigabitEthernet0/0/0/1
#  shutdown
# !
# interface GigabitEthernet0/0/0/2
#  vrf custB
#  ipv4 address 178.18.169.23 255.255.255.0
#  dot1q native vlan 30
# !
# interface GigabitEthernet0/0/0/3
#  vrf custB
#  ipv4 address 10.10.0.2 255.255.255.0
#  dot1q native vlan 1021
# !
"""

RETURN = """
before:
  description: The configuration prior to the model invocation
  returned: always
  type: list
  sample: The configuration returned will alwys be in the same format of the paramters above.
after:
  description: The resulting configuration model invocation
  returned: when changed
  type: list
  sample: The configuration returned will alwys be in the same format of the paramters above.
commands:
  description: The set of commands pushed to the remote device
  returned: always
  type: list
  sample: ['interface GigabitEthernet0/0/0/2', 'description: Configured by Ansible', 'shutdown']
"""

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.iosxr.argspec.interfaces.interfaces import InterfacesArgs
from ansible.module_utils.network.iosxr.config.interfaces.interfaces import Interfaces


def main():
    """
    Main entry point for module execution
    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=InterfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
