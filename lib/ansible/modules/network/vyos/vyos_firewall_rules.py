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
The module file for vyos_firewall_rules
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
module: vyos_firewall_rules
version_added: '2.10'
short_description: Manage firewall rule-set attributes on VyOS devices
description: This module manages firewall rule-set attributes on VyOS devices
notes:
  - Tested against VyOS 1.1.8 (helium).
  - This module works with connection C(network_cli). See L(the VyOS OS Platform Options,../network/user_guide/platform_vyos.html).
author:
   - Rohit Thakur (@rohitthakur2590)
options:
  config:
    description: A dictionary of Firewall rule-set options.
    type: list
    elements: dict
    suboptions:
      address_families:
        description:
          - A dictionary specifying the address family to which the Firewall rule-set belongs.
        type: list
        elements: dict
        suboptions:
          afi:
            description:
              - Specifies the type of rule-set.
            type: str
            choices: ['ipv4', 'ipv6']
            required: True
          rule_sets:
            description:
              - The Firewall rule-set list.
            type: list
            elements: dict
            suboptions:
              name:
               description:
                 - Firewall rule set name.
               type: str    
              default_action:
                description:
                  - Default action for rule-set.
                  - drop (Drop if no prior rules are hit (default))
                  - reject (Drop and notify source if no prior rules are hit)
                  - accept (Accept if no prior rules are hit)
                type: str
                choices: ['drop', 'reject', 'accept']
              description:
                description:
                  - Rule set description.
                type: str
              enable_default_log:
                description:
                  - Option to log packets hitting default-action.
              rules:
                description:
                  - A ditionary that specifies the rule-set configurations.
                type: list
                elements: dict
                suboptions:
                  number:
                    description:
                      - Rule number.
                    type: int
                    required: True 
                  description:
                    description:
                      - Description of this rule.
                    type: str
                  action:
                    description:
                      - Specifying the action.
                    type: str
                    choice: ['drop', 'reject', 'accept', 'inspect']
                  destination:
                    description:
                      - Specifying the destination parameters.
                    type: dict
                    suboptions:
                      address:
                        description:
                          - Destination ip address subnet or range.
                          - IPv4/6 address, subnet or range to match.
                          - Match everything except the specified address, subnet or range.
                          - Destination ip address subnet or range.
                        type: str
                      group:
                        description:
                          - Destination group.
                        type: dict
                        suboptions:
                          address_group:
                            description:
                              - Group of addresses.
                            type: str
                          network_group:
                            description:
                              - Group of networks.
                            type: str
                          port_group:
                            description:
                              - Group of ports.
                            type: str
                      port:
                       description:
                         - Multiple destination ports can be specified as a comma-separated list.
                         - The whole list can also be "negated" using '!'.
                         - For example:'!22,telnet,http,123,1001-1005'.
                       type: str      
                  disabled:
                    description:
                      - Option to disable firewall rule.
                    type: bool
                  fragment:
                    description:
                      - IP fragment match.
                    type: str
                    choices: ['match-frag', 'match-non-frag']
                  icmp:
                   description:
                     - ICMP type and code information.
                   type: dict
                   suboptions:
                     type_name:
                       description:
                         - ICMP type-name.
                       type: str
                       choices: ['any', 'echo-reply', 'destination-unreachable', 'network-unreachable', 'host-unreachable', 'protocol-unreachable', 
                                'port-unreachable','fragmentation-needed','source-route-failed', 'network-unknown', 'host-unknown', 'network-prohibited',
                                'host-prohibited', 'TOS-network-unreachable', 'TOS-host-unreachable', 'communication-prohibited', 'host-precedence-violation',
                                'precedence-cutoff', 'source-quench', 'redirect', 'network-redirect', 'host-redirect', 'TOS-network-redirect', 'TOS-host-redirect']
                     code:
                       description:
                         - ICMP code.
                       type: int
                     type:
                       description:
                         - ICMP type.
                       type: int
                  ipsec:
                    description:
                      - Inboud ip sec packets.
                    type: str
                    choices: ['match-ipsec', 'match-none']
                  limit:
                    description:
                      - Rate limit using a token bucket filter.
                    type: dict
                    suboptions:
                      burst:
                        description:
                          - Maximum number of packets to allow in excess of rate.
                        type: int
                      rate:
                        description:
                          - format for rate (integer/time unit).
                          - any one of second, minute, hour or day may be used to specify time unit.
                          - eg. 1/second implies rule to be matched at an average of once per second.
                        type: dict
                        suboptions:
                          number:
                            description:
                              - This is the integer value.
                            type: int
                          unit:
                            description:
                              - This is the time unit.
                            type: str
                  p2p:
                   description:
                     - P2P application packets.
                   type: list
                   choices: ['all', 'applejuice', 'bittorrent', 'directconnect', 'edonkey', 'gnutella', 'kazaa']
                  protocol:
                    description:
                      - Protocol to match (protocol name in /etc/protocols or protocol number or all).
                      - <text> IP protocol name from /etc/protocols (e.g. "tcp" or "udp").
                      - <0-255> IP protocol number.
                      - tcp_udp Both TCP and UDP.
                      - all All IP protocols.
                      - (!)All IP protocols except for the specified name or number.
                  recent:
                    description:
                      - Parameters for matching recently seen sources.
                    type: dict
                    suboptions:
                      count:
                        description:
                          - Source addresses seen more than N times.
                        type: int
                      time:
                        description:
                          - Source addresses seen in the last N seconds.
                        type: int
                  source:
                    description:
                      - Source parameters.
                    type: dict
                    suboptions:
                      address:
                        description:
                          - Source ip address subnet or range.
                          - IPv4/6 address, subnet or range to match.
                          - Match everything except the specified address, subnet or range.
                          - Source ip address subnet or range.
                        type: str
                      group:
                        description:
                          - Source group.
                        type: dict
                        suboptions:
                          address_group:
                            description:
                              - Group of addresses.
                            type: str
                          network_group:
                            description:
                              - Group of networks.
                            type: str
                          port_group:
                            description:
                              - Group of ports.
                            type: str
                      port:
                       description:
                         - Multiple source ports can be specified as a comma-separated list.
                         - The whole list can also be "negated" using '!'.
                         - For example:'!22,telnet,http,123,1001-1005'.
                       type: str
                      mac_address:
                        description:
                          - <MAC address> MAC address to match.
                          - <!MAC address> Match everything except the specified MAC address.
                        type: str    
                  state:
                    description:
                      - Session state.
                    type: dict
                    suboptions:
                      established:
                        description:
                          - Established state.
                        type: bool 
                      invalid:
                        description:
                          - Invalid state.
                        type: bool
                      new:
                        description:
                          - New state.
                        type: bool
                      related:
                        description:
                          - Related state.
                        type: bool
                  tcp:
                    description:
                      - TCP flags to match.
                    type: dict
                    suboptions:
                      flags:
                        description:
                          - TCP flags to be matched.
                        type: str
                  time:
                    description:
                      - Time to match rule.
                    type: dict
                    suboptions:
                      monthdays:
                        description:
                          - Monthdays to match rule on.
                        type: str    
                      startdate:
                        description:
                          - Date to start matching rule.
                        type: str
                      starttime:
                        description:
                          - Time of day to start matching rule.
                        type: str
                      stopdate:
                        description:
                          - Date to stop matching rule.
                        type: str
                      stoptime:
                        description:
                          - Time of day to stop matching rule.
                        type: str
                      weekdays:
                        description:
                          - Weekdays to match rule on.
                        type: str
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
        C(show configuration commands | grep 'firewall')
    version_added: "2.10"
    type: str
  state:
    description:
    - The state the configuration should be left in
    type: str
    choices:
    - merged
    - replaced
    - overridden
    - deleted
    - gathered
    - rendered
    - parsed
    default: merged
"""
EXAMPLES = """

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
  sample:
    - "set protocols static route 192.0.0.0/24 next-hop '192.11.11.11'"
    - "set protocols static route 192.0.0.0/24 'blackhole'"
rendered:
  description: The set of CLI commands generated from the value in C(config) option
  returned: When C(state) is I(rendered)
  type: list
  sample: >
    "address_families": [
                {
                    "afi": "ipv4",
                    "routes": [
                        {
                            "blackhole_config": {
                                "type": "blackhole"
                            },
                            "dest": "192.0.0.0/24",
                            "next_hops": [
                                {
                                    "forward_router_address": "192.11.11.11"
                                },
                                {
                                    "forward_router_address": "192.11.11.12"
                                }
                            ]
                        }
                    ]
                }
            ]
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
from ansible.module_utils.network.vyos.argspec.firewall_rules.firewall_rules import Firewall_rulesArgs
from ansible.module_utils.network.vyos.config.firewall_rules.firewall_rules import Firewall_rules


def main():
    """
    Main entry point for module execution
    :returns: the result form module invocation
    """
    required_if = [('state', 'merged', ('config',)),
                   ('state', 'replaced', ('config',)),
                   ('state', 'overridden', ('config',)),
                   ('state', 'parsed', ('running_config',))]
    mutually_exclusive = [('config', 'running_config')]

    module = AnsibleModule(argument_spec=Firewall_rulesArgs.argument_spec,
                           required_if=required_if,
                           supports_check_mode=True,
                           mutually_exclusive=mutually_exclusive)
    result = Firewall_rules(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
