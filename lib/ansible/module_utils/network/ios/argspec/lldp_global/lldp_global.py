#
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
The arg spec for the ios_lldp_global module
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type


class Lldp_globalArgs(object):

    def __init__(self, **kwargs):
        pass

    argument_spec = {'config': {'options': {'holdtime': {'type': 'int'},
                                            'reinit': {'type': 'int'},
                                            'enabled': {'type': 'bool'},
                                            'timer': {'type': 'int'},
                                            'tlv_select': {
                                                'options': {
                                                    'four_wire_power_management': {'type': 'bool'},
                                                    'mac_phy_cfg': {'type': 'bool'},
                                                    'management_address': {'type': 'bool'},
                                                    'port_description': {'type': 'bool'},
                                                    'port_vlan': {'type': 'bool'},
                                                    'power_management': {'type': 'bool'},
                                                    'system_capabilities': {'type': 'bool'},
                                                    'system_description': {'type': 'bool'},
                                                    'system_name': {'type': 'bool'}
                                                },
                                                'type': 'dict'},
                                            },
                                'type': 'dict'},
                     'state': {'choices': ['merged', 'replaced', 'deleted'],
                               'default': 'merged',
                               'type': 'str'}}
