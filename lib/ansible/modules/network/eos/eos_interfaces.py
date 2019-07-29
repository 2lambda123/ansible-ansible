#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2019 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

##############################################
#                 WARNING                    #
##############################################
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
##############################################

"""
The module file for eos_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: eos_interfaces
version_added: 2.9
short_description: Manages interface attributes of Arista EOS interfaces
description: ['This module manages the interface attributes of Arista EOS interfaces.']
author: ['Nathaniel Case (@qalthos)']
options:
  config:
    description: The provided configuration
    type: list
    suboptions:
      description:
        description:
        - Interface description
        type: str
      duplex:
        default: auto
        description:
        - Interface link status. Applicable for Ethernet interfaces only.
        - Values other than C(auto) must also set I(speed).
        - Ignored when I(speed) is set above C(1000).
        type: str
      enable:
        default: true
        description:
        - Administrative state of the interface.
        - Set the value to C(true) to administratively enable the interface or C(false)
          to disable it.
        type: bool
      mtu:
        description:
        - MTU for a specific interface. Must be an even number between 576 and 9216.
          Applicable for Ethernet interfaces only.
        type: str
      name:
        description:
        - Full name of the interface, e.g. GigabitEthernet1.
        type: str
      speed:
        description:
        - Interface link speed. Applicable for Ethernet interfaces only.
        type: str
  state:
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    default: merged
    description:
    - The state the configuration should be left in.
    type: str

"""

EXAMPLES = """
---

# Using merged

# Before state:
# -------------
#
# veos#show running-config | section interface
# interface Ethernet1
#    description "Interface 1"
# !
# interface Ethernet2
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

- name: Merge provided configuration with device configuration
  eos_interfaces:
    config:
      - name: Ethernet1
        enable: True
      - name: Ethernet2
        description: 'Configured by Ansible'
        enable: False
    state: merged

# After state:
# ------------
#
# veos#show running-config | section interface
# interface Ethernet1
#    description "Interface 1"
# !
# interface Ethernet2
#    description "Configured by Ansible"
#    shutdown
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

# Using replaced

# Before state:
# -------------
#
# veos#show running-config | section interface
# interface Ethernet1
#    description "Interface 1"
# !
# interface Ethernet2
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

- name: Replaces device configuration of listed interfaces with provided configuration
  eos_interfaces:
    config:
      - name: Ethernet1
        enable: True
      - name: Ethernet2
        description: 'Configured by Ansible'
        enable: False
    state: replaced

# After state:
# ------------
#
# veos#show running-config | section interface
# interface Ethernet1
# !
# interface Ethernet2
#    description "Configured by Ansible"
#    shutdown
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

# Using overridden

# Before state:
# -------------
#
# veos#show running-config | section interface
# interface Ethernet1
#    description "Interface 1"
# !
# interface Ethernet2
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

- name: Overrides all device configuration with provided configuration
  eos_interfaces:
    config:
      - name: Ethernet1
        enable: True
      - name: Ethernet2
        description: 'Configured by Ansible'
        enable: False
    state: overridden

# After state:
# ------------
#
# veos#show running-config | section interface
# interface Ethernet1
# !
# interface Ethernet2
#    description "Configured by Ansible"
#    shutdown
# !
# interface Management1
#    ip address dhcp
# !

# Using deleted

# Before state:
# -------------
#
# veos#show running-config | section interface
# interface Ethernet1
#    description "Interface 1"
# !
# interface Ethernet2
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !

- name: Delete or return interface parameters to default settings
  eos_interfaces:
    config:
      - name: Ethernet1
    state: deleted

# After state:
# ------------
#
# veos#show running-config | section interface
# interface Ethernet1
# !
# interface Ethernet2
# !
# interface Management1
#    description "Management interface"
#    ip address dhcp
# !
"""

RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  type: dict
  sample: The configuration returned will always be in the same format of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  type: dict
  sample: The configuration returned will always be in the same format of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.eos.config.interfaces.interfaces import Interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Interfaces.argument_spec,
                           supports_check_mode=True)

    result = Interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
