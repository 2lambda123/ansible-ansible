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
The module file for nxos_l3_interfaces
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}

DOCUMENTATION = """
---
module: nxos_l3_interfaces
version_added: 2.9
short_description: Manages Layer-3 Interfaces attributes of NX-OS Interfaces
description: This module manages Layer-3 interfaces attributes of NX-OS Interfaces.
author: Trishna Guha (@trishnaguha)
notes:
  - Tested against NXOS 7.3.(0)D1(1) on VIRL
options:
  config:
    description: A dictionary of Layer-3 interface options
    type: list
    elements: dict
    suboptions:
      name:
        description:
          - Full name of L3 interface, i.e. Ethernet1/1.
        type: str
        required: true
      ipv4:
        description:
          - IPv4 address and attributes of the L3 interface.
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - IPV4 address of the L3 interface.
            type: str
          tag:
            description:
              - URIB route tag value for local/direct routes.
            type: int
          secondary:
            description:
              - A boolean attribute to manage addition of secondary IP address.
            type: bool
            default: False
      ipv6:
        description:
          - IPv6 address and attributes of the L3 interface.
        type: list
        elements: dict
        suboptions:
          address:
            description:
              - IPV6 address of the L3 interface.
            type: str
          tag:
            description:
              - URIB route tag value for local/direct routes.
            type: int
  running_config:
    description:
      - The module, by default, will connect to the remote device and
        retrieve the current running-config to use as a base for comparing
        against the contents of source. There are times when it is not
        desirable to have the task get the current running-config for
        every task in a playbook.  The I(running_config) argument allows the
        implementer to pass in the configuration to use as the base
        config for comparison. This value of this option should be the
        output received from device by executing command
        C(show running-config | section ^interface)
    version_added: "2.10"
  state:
    description:
      - The state of the configuration after module completion. 
      - The states I(rendered), I(gathered) and I(parsed) does not perform any
        change on the device. 
      - The state I(rendered) will transform the configuration in C(config) option to platform
        specific CLI commands which will be returned in the I(rendered) key within the result.
        For state I(rendered) active connection to remote host is not required.
      - The state I(gathered) will fetch the running configuration from device and transform
        it into structured data in the format as per the resource module argspec and the
        value is returned in the I(gathered) key within the result.
      - The state I(parsed) reads the configuration from C(running_config) option and transforms
        it into JSON format as per the resource module parameters and the value is returned in
        the I(parsed) key within the result. The value of C(running_config) option should be the
        same format as the output of command I(show running-config | section ^interface) executed
        on device. For state I(parsed) active connection to remote host is not required.
    type: str
    choices:
      - merged
      - replaced
      - overridden
      - deleted
      - rendered
      - gathered
      - parsed
    default: merged
"""
EXAMPLES = """
# Using merged

# Before state:
# -------------
#
# interface Ethernet1/6

- name: Merge provided configuration with device configuration.
  nxos_l3_interfaces:
    config:
      - name: Ethernet1/6
        ipv4:
          - address: 192.168.1.1/24
            tag: 5
          - address: 10.1.1.1/24
            secondary: True
            tag: 10
        ipv6:
          - address: fd5d:12c9:2201:2::1/64
            tag: 6
    state: merged

# After state:
# ------------
#
# interface Ethernet1/6
#   ip address 192.168.22.1/24 tag 5
#   ip address 10.1.1.1/24 secondary tag 10
# interfaqce Ethernet1/6
#   ipv6 address fd5d:12c9:2201:2::1/64 tag 6


# Using replaced

# Before state:
# -------------
#
# interface Ethernet1/6
#   ip address 192.168.22.1/24
#   ipv6 address "fd5d:12c9:2201:1::1/64"

- name: Replace device configuration of specified L3 interfaces with provided configuration.
  nxos_l3_interfaces:
    config:
      - name: Ethernet1/6
        ipv4: 192.168.22.3/24
    state: replaced

# After state:
# ------------
#
# interface Ethernet1/6
#   ip address 192.168.22.3/24


# Using overridden

# Before state:
# -------------
#
# interface Ethernet1/2
#   ip address 192.168.22.1/24
# interface Ethernet1/6
#   ipv6 address "fd5d:12c9:2201:1::1/64"

- name: Override device configuration of all L3 interfaces on device with provided configuration.
  nxos_l3_interfaces:
    config:
      - name: Ethernet1/2
        ipv4: 192.168.22.3/4
    state: overridden

# After state:
# ------------
#
# interface Ethernet1/2
#   ipv4 address 192.168.22.3/24
# interface Ethernet1/6


# Using deleted

# Before state:
# -------------
#
# interface Ethernet1/6
#   ip address 192.168.22.1/24
# interface Ethernet1/2
#   ipv6 address "fd5d:12c9:2201:1::1/64"

- name: Delete L3 attributes of given interfaces (This won't delete the interface itself).
  nxos_l3_interfaces:
    config:
      - name: Ethernet1/6
      - name: Ethernet1/2
    state: deleted

# After state:
# ------------
#
# interface Ethernet1/6
# interface Ethernet1/2


"""
RETURN = """
before:
  description: The configuration as structured data prior to module invocation.
  returned: always
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The configuration as structured data after module completion.
  returned: when changed
  type: list
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
commands:
  description: The set of commands pushed to the remote device.
  returned: always
  type: list
  sample: ['interface Ethernet1/2', 'ip address 192.168.0.1/2']
rendered:
  description: The set of CLI commands generated from the value in C(config) option
  returned: When C(state) is I(rendered)
  type: list
  sample: ['interface Ethernet1/1', 'mtu 1800']
gathered:
  description: The configuration as structured data transformed for the running configuration
               fetched from remote host
  returned: When C(state) is I(gathered)
  type: list
  sample: >
    The configuration returned will always be in the same format
    of the parameters above.
parsed:
  description: The configuration as structured data transformed for the value of
               C(running_config) option
  returned: When C(state) is I(parsed)
  type: list
  sample: >
    The configuration returned will always be in the same format
    of the parameters above.
"""


from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.nxos.argspec.l3_interfaces.l3_interfaces import L3_interfacesArgs
from ansible.module_utils.network.nxos.config.l3_interfaces.l3_interfaces import L3_interfaces


def main():
    """
    Main entry point for module execution

    :returns: the result form module invocation
    """
    required_if = [['state', 'parsed', ['running_config']]]
    mutually_exclusive = [('config', 'running_config')]

    module = AnsibleModule(argument_spec=L3_interfacesArgs.argument_spec,
                           supports_check_mode=True,
                           required_if=required_if,
                           mutually_exclusive=mutually_exclusive)

    result = L3_interfaces(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
