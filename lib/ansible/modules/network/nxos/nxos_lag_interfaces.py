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
The module file for nxos_lag_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
  'metadata_version': '1.1',
  'status': ['preview'],
  'supported_by': 'network'
}

DOCUMENTATION = """
---
module: nxos_lag_interfaces
version_added: 2.9
short_description: Manages link aggregation groups of NX-OS Interfaces
description: This module manages attributes of link aggregation groups of NX-OS Interfaces.
author: Trishna Guha (@trishnaguha)
options:
  config:
    description: A list of link aggregation group configurations.
    type: list
    elements: dict
    suboptions:
      id:
        description:
          - ID of the link aggregation group (LAG).
        type: int
        required: true
      members:
        description:
          - The list of interfaces that are part of the group.
        type: list
        required: true
        elements: dict
        suboptions:
          member:
            description:
              - The interface name.
          type: str
          mode:
            description:
              - Link aggregation group (LAG).
            type: str
            choices:
              - active
              - on
              - passive
          force:
            description:
              - When true it forces link aggregation group members to match what
                is declared in the members param. This can be used to remove members.
            type: bool
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
    default: merged
notes:
  - Tested against NXOS 7.3.(0)D1(1) on VIRL.
  - This module works with connection C(network_cli).
"""
EXAMPLES = """
# Using merged

# Before state:
# -------------
#
# interface Ethernet1/4

- name: Merge provided configuration with device configuration.
  nxos_lag_interfaces:
    config:
      - id: 99
        members:
          - member: Ethernet1/4
    state: merged

# After state:
# ------------
#
# interface Ethernet1/4
#   channel-group 99


# Using replaced

# Before state:
# -------------
#
# interface Ethernet1/4
#   channel-group 99 mode active

- name: Replace device configuration of specified LAG attributes of given interfaces with provided configuration.
  nxos_lag_interfaces:
    config:
      - id: 10
        members:
          - member: Ethernet1/4
    state: replaced

# After state:
# ------------
#
# interface Ethernet1/4
#   channel-group 10


# Using overridden

# Before state:
# -------------
#
# interface Ethernet1/4
#   channel-group 10
# interface Ethernet1/2
#   channel-group 99 mode passive

- name: Override device configuration of all LAG attributes of given interfaces on device with provided configuration.
  nxos_lag_interfaces:
    config:
      - id: 20
        members:
          - member: Ethernet1/6
            force: True
    state: overridden

# After state:
# ------------
# interface Ethernet1/2
# interface Ethernet1/4
# interface Ethernet1/6
#   channel-group 20 force


# Using deleted

# Before state:
# -------------
#
# interface Ethernet1/4
#   channel-group 99 mode active

- name: Delete LAG attributes of given interface (Note: This won't delete the port-channel itself).
  nxos_lag_interfaces:
    config:
      - id: 99
    state: deleted

- name: Delete LAG attributes of all the interfaces
  nxos_lag_interfaces:
    state: deleted

# After state:
# ------------
#
# interface Ethernet1/4
#   no channel-group 99


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['command 1', 'command 2', 'command 3']
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.argspec.lag_interfaces.lag_interfaces import Lag_interfacesArgs
from ansible.module_utils.network.nxos.config.lag_interfaces.lag_interfaces import Lag_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    module = AnsibleModule(argument_spec=Lag_interfacesArgs.argument_spec,
                           supports_check_mode=True)

    result = Lag_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
