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
The module file for eos_acls
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
module: eos_acls
version_added: '2.10'
short_description: 'Manages IP access-list attributes of Arista EOS interfaces'
description: This module manages the IP access-list attributes of Arista EOS interfaces.
author: Gomathiselvi S (@GomathiselviS)
notes:
- Tested against Arista vEOS v4.20.10M
options:
  config:
    description: A dictionary of IP access-list options
    type: list
    elements: dict
    suboptions:
      afi:
        description:
          - The Address Family Indicator (AFI) for the Access Control Lists (ACL).
        type: str
        required: true
        choices: ['ipv4', 'ipv6']
      acls:
        description:
        - A list of Access Control Lists (ACL).
        type: list
        elements: dict
        suboptions:
          standard: 
            description: standard access-list or not 
            type: bool
            default: False
          name:
            description: Name of the acl-list
            type: str
            required: true
          aces:
            description: Filtering data
            type: list
            element: dict
            suboptions:
              sequence:
                description: sequence number for the ordered list of rules
                type: int
              remark:
                description: Specify a comment
                type: str
              fragment_rules:
                description: Add fragment rules
                type: bool
              grant:
                description: Action to be applied on the rule
                type: str
                choice: ['permit', 'deny']
              protocol:
                description:
                      - Specify the protocol to match.
                      - Refer to vendor documentation for valid values.
                type: str
              vlan:
                description: Vlan options
                type: str
              protocol_options:
                description: All the possible sub options for the protocol chosen.
                type: dict
                element: dict
                suboptions:
                  tcp:
                    description: Options for tcp protocol.
                    type: dict
                    suboptions:
                      flags:
                        description: Match TCP packet flags
                        type: dict
                        suboptions:
                          ack:
                            description: Match on the ACK bit
                            type: bool
                          established:
                            description: Match established connections
                            type: bool
                          fin:
                            description: Match on the FIN bit
                            type: bool
                          psh:
                            description: Match on the PSH bit
                            type: bool
                          rst:
                            description: Match on the RST bit
                            type: bool
                          syn:
                            description: Match on the SYN bit
                            type: bool
                          urg:
                            description: Match on the URG bit
                            type: bool
                  icmp:
                    description:
                      - Internet Control Message Protocol settings.
                    type: dict
                    suboptions:
                      administratively_prohibited:
                        description: Administratively prohibited
                        type: bool
                      alternate_address:
                        description: Alternate address
                        type: bool
                      conversion_error:
                        description: Datagram conversion
                        type: bool
                      dod_host_prohibited:
                        description: Host prohibited
                        type: bool
                      dod_net_prohibited:
                        description: Net prohibited
                        type: bool
                      echo:
                        description: Echo (ping)
                        type: bool
                      echo_reply:
                        description: Echo reply
                        type: bool
                      general_parameter_problem:
                        description: Parameter problem
                        type: bool
                      host_isolated:
                        description: Host isolated
                        type: bool
                      host_precedence_unreachable:
                        description: Host unreachable for precedence
                        type: bool
                      host_redirect:
                        description: Host redirect
                        type: bool
                      host_tos_redirect:
                        description: Host redirect for TOS
                        type: bool
                      host_tos_unreachable:
                        description: Host unreachable for TOS
                        type: bool
                      host_unknown:
                        description: Host unknown
                        type: bool
                      host_unreachable:
                        description: Host unreachable
                        type: bool
                      information_reply:
                        description: Information replies
                        type: bool
                      information_request:
                        description: Information requests
                        type: bool
                      mask_reply:
                        description: Mask replies
                        type: bool
                      mask_request:
                        description: Mask requests
                        type: bool
                      message_code:
                        description: ICMP message code
                        type: int
                      message_type:
                        description: ICMP message type
                        type: int
                      mobile_redirect:
                        description: Mobile host redirect
                        type: bool
                      net_redirect:
                        description: Network redirect
                        type: bool
                      net_tos_redirect:
                        description: Net redirect for TOS
                        type: bool
                      net_tos_unreachable:
                        description: Network unreachable for TOS
                        type: bool
                      net_unreachable:
                        description: Net unreachable
                        type: bool
                      network_unknown:
                        description: Network unknown
                        type: bool
                      no_room_for_option:
                        description: Parameter required but no room
                        type: bool
                      option_missing:
                        description: Parameter required but not present
                        type: bool
                      packet_too_big:
                        description: Fragmentation needed and DF set
                        type: bool
                      parameter_problem:
                        description: All parameter problems
                        type: bool
                      port_unreachable:
                        description: Port unreachable
                        type: bool
                      precedence_unreachable:
                        description: Precedence cutoff
                        type: bool
                      protocol_unreachable:
                        description: Protocol unreachable
                        type: bool
                      reassembly_timeout:
                        description: Reassembly timeout
                        type: bool
                      redirect:
                        description: All redirects
                        type: bool
                      router_advertisement:
                        description: Router discovery advertisements
                        type: bool
                      router_solicitation:
                        description: Router discovery solicitations
                        type: bool
                      source_quench:
                        description: Source quenches
                        type: bool
                      source_route_failed:
                        description: Source route failed
                        type: bool
                      time_exceeded:
                        description: All time exceededs
                        type: bool
                      timestamp_reply:
                        description: Timestamp replies
                        type: bool
                      timestamp_request:
                        description: Timestamp requests
                        type: bool
                      traceroute:
                        description: Traceroute
                        type: bool
                      ttl_exceeded:
                        description: TTL exceeded
                        type: bool
                      unreachable:
                        description: All unreachables
                        type: bool
                      message_num:
                        description: icmp msg type number.
                        type: int
                  icmpv6:
                    description: Options for icmpv6.
                    type: dict
                    suboptions:
                      address_unreachable:
                        description: address unreachable
                        type: bool
                      beyond_scope:
                        description: beyond_scope
                        type: bool
                      echo_reply:
                        description: echo_reply
                        type: bool
                      echo_request:
                        description: echo reques
                        type: bool
                      erroneous_header:
                        description: erroneous header
                        type: bool
                      fragment_reassembly_exceeded:
                        description: fragment_reassembly_exceeded
                        type: bool
                      hop_limit_exceeded:
                        description: hop limit exceeded
                        type: bool
                      neighbor_advertisement:
                        description: neighbor advertisement
                        type: bool
                      neighbor_solicitation:
                        description: neighbor_solicitation
                        type: bool
                      no_admin:
                        description: no admin
                        type: bool
                      no_route:
                        description: no route
                        type: bool
                      packet_too_big:
                        description: packet too big
                        type: bool
                      parameter_problem:
                        description: parameter problem
                        type: bool 
                      port_unreachable:
                        description: port unreachable
                        type: bool
                      redirect_message:
                        description: redirect message
                        type: bool
                      reject_route:
                        description: reject route
                        type: bool
                      router_advertisement:
                        description: router_advertisement
                        type: bool
                      router_solicitation:
                        description: router_solicitation
                        type: bool
                      source_address_failed:
                        description: source_address_failed
                        type: bool
                      source_routing_error:
                        description: source_routing_error
                        type: bool
                      time_exceeded:
                        description: time_exceeded
                        type: bool
                      unreachable:
                        description: unreachable
                        type: bool
                      unrecognized_ipv6_option:
                        description: unrecognized_ipv6_option
                        type: bool
                      unrecognized_next_header:
                        description: unrecognized_next_header
                        type: bool
                  ip:
                    description : Internet Protocol.
                    type: dict
                    suboptions:
                      nexthop_group:
                        description: Nexthop-group name.
                        type: str
                  ipv6:
                    description : Internet V6 Protocol.
                    type: dict
                    suboptions:
                      nexthop_group:
                        description: Nexthop-group name.
                        type: str
              source:
                description: The packet's source address
                type: dict
                suboptions:
                  address:
                    description:  dotted decimal notation of IP address
                    type: str
                  wildcard_bits:
                    description: Source wildcard bits
                    type: str
                  subnet_address:
                    description:  A subnet address
                    type: str
                  host:
                    description:  Host IP address
                    type:  str
                  any:
                    description:  Rule matches all source addresses
                    type: bool
                  port_protocol:
                    description: Specify source port/protocoli, along with operator. (comes with tcp/udp).
                    type: dict
              destination:
                description: The packet's destination address
                type: dict
                suboptions:
                  address:
                    description:  dotted decimal notation of IP address
                    type: str
                  wildcard_bits:
                    description: Source wildcard bits
                    type: str
                  subnet_address:
                    description:  A subnet address
                    type: str
                  host:
                    description:  Host IP address
                    type:  str
                  any:
                    description:  Rule matches all source addresses
                    type: bool
                  port_protocol:
                    description: Specify dest port/protocol, along with operator . (comes with tcp/udp).
                    type: dict
              ttl:
                description:  Compares the TTL (time-to-live) value in the packet to a specified value
                type: dict
                suboptions:
                  eq:
                    description:  Match a single TTL value
                    type: int
                  lt:
                    description: Match TTL lesser than this number
                    type: int
                  gt:
                    description: Match TTL greater than this number
                    type: int
                  neq:
                    description:  Match TTL not equal to this value
                    type: int
              fragments:
                description: Match non-head fragment packets
                type: bool
              log:
                description:  Log matches against this rule
                type: bool
              tracked:
                description: Match packets in existing ICMP/UDP/TCP connections
                type: bool
              hop_limit:
                description: Hop limit value.
                type: dict
  state:
    description:
      - The state the configuration should be left in.
    type: str
    choices:
      ['deleted', 'merged', 'overridden', 'replaced', 'gathered', 'rendered', 'parsed']
    default:
      merged
"""
EXAMPLES = """
# Using merged

# Before state:
# -------------
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log 
#    40 permit ip any any
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20



- name: Merge provided configuration with device configuration
  eos_acls:
    config:
     - afi: "ipv4"
      	- name: test1
          aces:
	  - sequence: 35
	    grant: "deny"
	    protocol: "ospf"
	    source:
	      subnetaddress: 20.0.0.0/8
            dest:
              any: true
    state: merged

# After state:
# ------------
#
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log 
#    35 deny ospf 20.0.0.0/8 any
#    40 permit ip any any
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20


# Using replaced

# Before state:
# -------------
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log 
#    40 permit ip any any
# !
# ip access-list test3
#    10 permit ip 35.33.0.0/16 any log
# !
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20



- name: Replace device configuration with provided configuration 
  eos_acls:
    config:
      - afi: "ipv4"
        - name: test1
          aces:
	  - sequence: 35
	    grant: "permit"
	    protocol: "ospf"
	    source:
	      subnetaddress: 20.0.0.0/8
            dest:
              any: true
    state: replaced

# After state:
# ------------
#
# show running-config | section access-list
# ip access-list test1
#    35 permit ospf 20.0.0.0/8 any
# !
# ip access-list test3
#    10 permit ip 35.33.0.0/16 any log 
# !
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20


# Using overridden

# Before state:
# -------------
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log 
#    40 permit ip any any
# !
# ip access-list test3
#    10 permit ip 35.33.0.0/16 any log
# !
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20



- name: override device configuration with  provided configuration
  eos_acls:
    config:
      - afi: "ipv4"
        - name: test1
          aces:
	  - sequence: 35
	    action: "permit"
	    protocol: "ospf"
	    source:
	      subnetaddress: 20.0.0.0/8
            dest:
              any: true
    state: overridden

# After state:
# ------------
#
# show running-config | section access-list
# ip access-list test1
#    35 permit ospf 20.0.0.0/8 any
# !


# Using deleted

# Before state:
# -------------
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log 
#    40 permit ip any any
# !
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20


- name: Delete provided configuration 
  eos_acls:
    config:
      - afi: "ipv4"
      	- name: test1
          aces:
	  - sequence: 30
    state: deleted

# After state:
# ------------
#
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    40 permit ip any any
# !
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20



# Before state:
# -------------
# show running-config | section access-list
# ip access-list test1
#    10 permit ip 10.10.10.0/24 any ttl eq 200
#    20 permit ip 10.30.10.0/24 host 10.20.10.1
#    30 deny tcp host 10.10.20.1 eq finger www any syn log
#    40 permit ip any any
# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20

# !

- name: Delete provided configuration
  eos_acls:
    config:
     - afi: "ipv4"
       - name: test1
    state: deleted

# After state:
# ------------
#
# show running-config | section access-list

# ipv6 access-list test2
#     10 deny icmpv6 any any reject-route hop-limit eq 20


# using gathered

ip access-list test1
    35 deny ospf 20.0.0.0/8 any
ip access-list test2
    40 permit vlan 55 0xE2 icmpv6 any any log

- name: Gather the exisitng condiguration
  eos_acls:
    state: gathered

# returns:

eos_acls:
    config:
     - afi: "ipv4"
        - name: test1
          aces:
          - sequence: 35
            grant: "deny"
            protocol: "ospf"
            source:
              subnetaddress: 20.0.0.0/8
            dest:
              any: true
    - afi: "ipv6"
      - name: test2
        aces:
	 - sequence: 40
           grant: "permit"
           vlan: "55 0xE2"
           protocol: "icmpv6"
           log: true
           source:
             any: true
           dest:
             any: true


returns:

  eos_acls:
    config:
     - afi: "ipv4"
        - name: test1
          aces:
          - sequence: 35
            grant: "deny"
            protocol: "ospf"
            source:
              subnetaddress: 20.0.0.0/8
            dest:
              any: true


# using rendered

eos_acls:
    config:
     - afi: "ipv4"
        - name: test1
          aces:
          - sequence: 35
            grant: "deny"
            protocol: "ospf"
            source:
              subnetaddress: 20.0.0.0/8
            dest:
              any: true
    - afi: "ipv6"
      - name: test2
        aces:
	 - sequence: 40
           grant: "permit"
           vlan: "55 0xE2"
           protocol: "icmpv6"
           log: true
           source:
             any: true
           dest:
             any: true

returns:

ip access-list test1
    35 deny ospf 20.0.0.0/8 any
ip access-list test2
    40 permit vlan 55 0xE2 icmpv6 any any log


"""
RETURN = """
before:
  description: The configuration prior to the model invocation.
  returned: always
  sample: >
    The configuration returned will always be in the same format
     of the parameters above.
after:
  description: The resulting configuration model invocation.
  returned: when changed
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
from ansible.module_utils.network.eos.argspec.acls.acls import AclsArgs
from ansible.module_utils.network.eos.config.acls.acls import Acls


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

    module = AnsibleModule(argument_spec=AclsArgs.argument_spec,
                           required_if=required_if,
                           supports_check_mode=True,
                           mutually_exclusive=mutually_exclusive)


    result = Acls(module).execute_module()
    module.exit_json(**result)


if __name__ == '__main__':
    main()
