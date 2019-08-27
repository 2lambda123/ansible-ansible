#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2019 NTT Communications Cloud Infrastructure Services
#
# This module is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software.  If not, see <http://www.gnu.org/licenses/>.
#
# Authors:
#   - Ken Sinfield (@kensinfield)
#
# NTT LTD MCP Cloud API Provider (MCP 2.0)

from __future__ import (absolute_import, division, print_function)

try:
    import requests as REQ
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
import struct
import socket
try:
    from ipaddress import (ip_address as ip_addr)
    HAS_IPADDRESS = True
except ImportError:
    HAS_IPADDRESS = False
from ansible.module_utils.ntt_mcp.ntt_mcp_config import (HTTP_HEADERS, API_VERSION, API_ENDPOINTS, DEFAULT_REGION)
from ansible.module_utils.ntt_mcp.ntt_mcp_utils import get_ip_version, IP_TO_INT, INT_TO_IP

class NTTMCPAPIException(Exception):
    """
    Custom exception to handle Cloud Control API exceptions

    :arg Exception: The exception generated
    :returns: Exception string
    """
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return "<NTTMCPAPIException: msg='%s'>" % (self.msg)

    def __repr__(self):
        return "<NTTMCPAPIException: msg='%s'>" % (self.msg)


class NTTMCPClient():
    """
    Class to handle all interfacing into the Cloud Control API
    """
    def __init__(self, credentials, region):
        self.check_imports()
        self.credentials = credentials
        self.region = region
        self.home_geo = self.get_user_home_geo()
        self.org_id = self.get_org_id()
        self.base_url = ('https://%s/caas/%s/%s/' % (API_ENDPOINTS[region]['host'], API_VERSION, self.org_id))

    def __repr__(self):
        return ('Username: %s\nHome Geo: %s\nOrg Id: %s\nSupplied Region: %s'
                '\nBase URL: %s' % (self.credentials[0], self.home_geo, self.org_id, self.region, self.base_url))

    def check_imports(self):
        """
        Check if the required Python modules for ntt_mcp_provider are installed
        """
        if not HAS_REQUESTS:
            raise NTTMCPAPIException('Missing Python module: requests')
        if not HAS_IPADDRESS:
            raise NTTMCPAPIException('Missing Python module: ipaddress')

    def get_user_home_geo(self):
        """
        Return the users home Cloud Control Geo

        :arg self: self
        :returns: The users home geo
        """
        url = ('https://%s/caas/%s/user/myUser' %
               (API_ENDPOINTS[DEFAULT_REGION]['host'], API_VERSION))
        response = self.api_get_call(url, None)
        if response != None:
            return response.json()['organization']['homeGeoApiHost']
        else:
            raise NTTMCPAPIException('Could not determine the Home Geo for user: %s') % (self.credentials[0])

    def get_org_id(self):
        """
        Get the org ID for the API credentials

        :arg self: self
        :returns: The UUID of the org ID for the account
        """
        url = ('https://%s/caas/%s/user/myUser' %
               (API_ENDPOINTS[DEFAULT_REGION]['host'], API_VERSION))
        response = self.api_get_call(url, None)
        if response != None:
            return response.json()['organization']['id']
        else:
            raise NTTMCPAPIException('Could not determine the Org Id for user: %s') % (self.credentials[0])


    '''
    NETWORK FUNCTIONS
    '''
    def list_network_domains(self, network_domain_id=None, datacenter=None, name=None, network_type=None, state=None):
        """
        Return a list of Cloud Network domains

        :arg self: self
        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw datacenter: The MCP name
        :kw name: The name of a Cloud Network Domain
        :kw network_type: The type of Cloud Network Domain(s)
        :kw state: The state of the Cloud Network Domain(s)
        :returns: An array of Cloud Network Domain dicts
        """
        params = {}
        if network_domain_id:
            params['id'] = network_domain_id
        if datacenter:
            params['datacenterId'] = datacenter
        if name:
            params['name'] = name
        if network_type:
            params['type'] = network_type
        if state:
            params['state'] = state

        url = self.base_url + 'network/networkDomain'

        response = self.api_get_call(url, params)
        if response != None:
            if response.json()['totalCount'] > 0:
                return response.json()['networkDomain']
            else:
                raise NTTMCPAPIException('No Network Domain found with the parameters {0}'.format(str(params)))
        else:
            raise NTTMCPAPIException('Could not get a list of network domains')


    def get_network_domain_by_name(self, name=None, datacenter=None):
        """
        Return a Cloud Network domain for the specified name

        :arg self: self
        :kw datacenter: The MCP name
        :kw name: The name of a Cloud Network Domain
        :returns: A Cloud Network Domain dict
        """
        if name is None:
            raise NTTMCPAPIException('A Cloud Network Domain is required.')
        if datacenter is None:
            raise NTTMCPAPIException('A Datacenter is required.')

        try:
            networks = self.list_network_domains(datacenter=datacenter)
        except Exception as e:
            raise NTTMCPAPIException('Failed to get a list of Cloud Network Domains - {0}'.format(e))
        network_exists = [x for x in networks if x['name'] == name]
        try:
            return network_exists[0]
        except IndexError as e:
            return None


    def create_network_domain(self, datacenter=None, name=None, network_type=None, description=None):
        """
        Create a Cloud Network domain

        :arg self: self
        :kw datacenter: The MCP name
        :kw name: The name of a Cloud Network Domain
        :kw network_type: The type of Cloud Network Domain
        :kw description: The description of the Cloud Network Domain
        :returns: The API response
        """
        params = {}
        if datacenter:
            params['datacenterId'] = datacenter
        if name:
            params['name'] = name
        if network_type:
            params['type'] = network_type
        if description:
            params['description'] = description

        url = self.base_url + 'network/deployNetworkDomain'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the create Cloud Network Domain request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def update_network_domain(self, network_domain_id=None, name=None, network_type=None, description=None):
        """
        Update an existing Cloud Network domains

        :arg self: self
        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw name: The name of a Cloud Network Domain
        :kw network_type: The type of Cloud Network Domain
        :kw description: The description of the Cloud Network Domain
        :returns: The API response
        """
        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Cloud Network Domain is required')

        params['id'] = network_domain_id
        if name:
            params['name'] = name
        if network_type:
            params['type'] = network_type
        if description:
            params['description'] = description

        url = self.base_url + 'network/editNetworkDomain'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the update Cloud Network Domain request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def delete_network_domain(self, network_domain_id=None):
        """
        Delete a Cloud Network domains

        :arg self: self
        :arg network_domain_id: The UUID of the Cloud Network Domain
        :returns: The API response
        """
        params = {}
        if network_domain_id:
            params['id'] = network_domain_id
        else:
            raise NTTMCPAPIException('No Cloud Network Domain ID supplied')

        url = self.base_url + 'network/deleteNetworkDomain'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the delete '
                                         'Cloud Network Domain request was '
                                         'accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def list_vlans(self, datacenter=None, network_domain_id=None, name=None, ipv4_network_address=None,
                   ipv6_network_address=None, state=None, attached=None):
        """
        Return a list of VLANs

        :arg self: self
        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw datacenter: The MCP name
        :kw name: The name of a VLAN
        :kw ipv4_network_address: The IPv4 subnet address of the VLAN
        :kw ipv6_network_address: The IPv6 subnet address of the VLAN
        :kw state: The state of the VLAN
        :kw attached: Is the VLAN attached
        :returns: An array of VLAN dicts
        """
        params = {}
        if datacenter:
            params['datacenterId'] = datacenter
        if network_domain_id:
            params['networkDomainId'] = network_domain_id
        if name:
            params['name'] = name
        if ipv4_network_address:
            params['privateIpv4Address'] = ipv4_network_address
        if ipv6_network_address:
            params['ipv6Address'] = ipv6_network_address
        if state:
            params['state'] = state
        if attached:
            params['attached'] = attached

        url = self.base_url + 'network/vlan'
        response = self.api_get_call(url, params)
        if response != None:
            if 'vlan' in response.json():
                return response.json()['vlan']
            else:
                return []
        else:
            raise NTTMCPAPIException('Could not get a list of VLANs')


    def get_vlan_by_name(self, name=None, datacenter=None, network_domain_id=None):
        """
        Return a VLAN for the specified name

        :kw self: self
        :kw datacenter: The MCP name
        :kw network_domain_id: The UUID of a Cloud Network Domain
        :returns: A VLAN dict
        """
        if name is None:
            raise NTTMCPAPIException('A VLAN is required.')
        try:
            vlans = self.list_vlans(datacenter=datacenter, network_domain_id=network_domain_id)
        except Exception as e:
            raise NTTMCPAPIException('Failed to get a list of VLANs - {0}'.format(e))

        vlan_exists = [x for x in vlans if x['name'] == name]
        try:
            return vlan_exists[0]
        except IndexError as e:
            return None


    def create_vlan(self,
                    networkDomainId=None,
                    name=None,
                    description=None,
                    privateIpv4NetworkAddress=None,
                    privateIpv4PrefixSize=None,
                    attachedVlan=False,
                    detachedVlan=False,
                    attachedVlan_gatewayAddressing=None,
                    detachedVlan_ipv4GatewayAddress=None
                   ):
        """
        Create a VLAN
        """
        params = {}
        if name:
            params['name'] = name
        if description:
            params['description'] = description
        if networkDomainId:
            params['networkDomainId'] = networkDomainId
        if privateIpv4NetworkAddress:
            params['privateIpv4NetworkAddress'] = privateIpv4NetworkAddress
        if privateIpv4PrefixSize:
            params['privateIpv4PrefixSize'] = privateIpv4PrefixSize
        if attachedVlan:
            params['attachedVlan'] = {}
            params['attachedVlan']['gatewayAddressing'] = (
                attachedVlan_gatewayAddressing)
        elif detachedVlan:
            params['detachedVlan'] = {}
            params['detachedVlan']['ipv4GatewayAddress'] = (
                detachedVlan_ipv4GatewayAddress)

        url = self.base_url + 'network/deployVlan'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the create VLAN request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')

    def update_vlan(self,
                    vlan_id=None,
                    name=None,
                    description=None,
                    detached_vlan_gw=None,
                    detached_vlan_gw_ipv6=None
                   ):
        """
        Update an existing VLAN
        """
        params = {}

        if vlan_id:
            params['id'] = vlan_id
        else:
            raise NTTMCPAPIException('A valid VLAN id is required')
        if name:
            params['name'] = name
        if description:
            params['description'] = description
        if detached_vlan_gw:
            params['ipv4GatewayAddress'] = detached_vlan_gw
        if detached_vlan_gw_ipv6:
            params['ipv6GatewayAddress'] = detached_vlan_gw_ipv6

        url = self.base_url + 'network/editVlan'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the update VLAN request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def delete_vlan(self, vlan_id=None):
        """
        Delete a VLAN
        """
        params = {}
        if vlan_id:
            params['id'] = vlan_id
        else:
            raise NTTMCPAPIException('No VLAN ID supplied')

        url = self.base_url + 'network/deleteVlan'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the delete VLAN request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def list_servers(self, datacenter=None, network_domain_id=None, vlan_id=None, name=None):
        """
        Return a list of servers/VMs
        """
        params = {}
        if datacenter is None:
            raise NTTMCPAPIException('A valid value for datacenter is required')
        else:
            params['datacenterId'] = datacenter
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid value for network_domain is required')
        else:
            params['networkDomainId'] = network_domain_id
        if vlan_id:
            params['vlanId'] = vlan_id
        if name:
            params['name'] = name

        url = self.base_url + 'server/server'

        response = self.api_get_call(url, params)
        if response != None:
            if 'server' in response.json():
                return response.json()['server']
            else:
                return []
        else:
            raise NTTMCPAPIException('Could not get a list of servers')


    def get_server_by_name(self, datacenter=None, network_domain_id=None, vlan_id=None, name=None):
        """
        Get a server/VM by name
        """
        if datacenter is None:
            raise NTTMCPAPIException('A valid value for datacenter is required')
        if name is None:
            raise NTTMCPAPIException('A valid value for name is required')

        servers = self.list_servers(datacenter, network_domain_id, vlan_id, name)
        server_exists = [x for x in servers if x['name'] == name]
        if server_exists:
            try:
                return server_exists[0]
            except (KeyError, IndexError):
                raise NTTMCPAPIException('Could not return the server object. Possible API error')
        else:
            return None


    def create_server(self, ngoc, params):
        """
        Create a VM
        """
        if ngoc:
            url = self.base_url + 'server/deployUncustomizedServer'
        else:
            url = self.base_url + 'server/deployServer'
        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the create server request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def reconfigure_server(self, params):
        """
        Change a VM specifications

        :arg params: dict of valid parameters
        :returns: An API message
        """
        url = self.base_url + 'server/reconfigureServer'
        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the update '
                                         'server request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def delete_server(self, server_id=None):
        """
        Delete a VM
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')

        url = self.base_url + 'server/deleteServer'

        response = self.api_post_call(url, params)
        if response != None:
            if response.json()['requestId'] != None:
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the delete Server request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def shutdown_server(self, server_id=None):
        """
        Shutdown a VM
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')

        url = self.base_url + 'server/shutdownServer'
        response = self.api_post_call(url, params)
        if response != None:
            if 'requestId' in response.json():
                return response.json()
            elif 'responseCode' in response.json():
                if response.json()['responseCode'] == 'SERVER_STOPPED':
                    return {}
                else:
                    raise NTTMCPAPIException('Could not confirm that the '
                                             'shutdown server request was '
                                             'accepted')
            else:
                raise NTTMCPAPIException('Could not confirm that the '
                                         'shutdown server request was '
                                         'accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def poweroff_server(self, server_id=None):
        """
        Hard power off a VM
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')

        url = self.base_url + 'server/powerOffServer'
        response = self.api_post_call(url, params)
        if response != None:
            if 'requestId' in response.json():
                return response.json()
            elif 'responseCode' in response.json():
                if response.json()['responseCode'] == 'SERVER_STOPPED':
                    return {}
                else:
                    raise NTTMCPAPIException('Could not confirm that the '
                                             'poweroff server request was '
                                             'accepted')
            else:
                raise NTTMCPAPIException('Could not confirm that the '
                                         'poweroff server request was '
                                         'accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def start_server(self, server_id=None):
        """
        Power on a VM
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')

        url = self.base_url + 'server/startServer'
        response = self.api_post_call(url, params)
        if response != None:
            if 'requestId' in response.json():
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the start server request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')

    def reboot_server(self, server_id=None):
        """
        Reboot a VM
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')

        url = self.base_url + 'server/rebootServer'
        response = self.api_post_call(url, params)
        if response != None:
            if 'requestId' in response.json():
                return response.json()
            else:
                raise NTTMCPAPIException('Could not confirm that the reboot server request was accepted')
        else:
            raise NTTMCPAPIException('No response from the API')


    def add_disk(self, controller_id=None, controller_name=None,
                 device_number=None, size=None, speed=None, iops=None):
        """
        Add a disk to an existing server
        """
        params = {}

        device_num_attribute_name = controller_name.replace('Controller', 'Id')

        if controller_id is not None and controller_name:
            params[controller_name] = {}
            params[controller_name]['controllerId'] = controller_id
        else:
            raise NTTMCPAPIException('Invalid storage controller')
        if device_number is not None and type(device_number) is int:
            params[controller_name][device_num_attribute_name] = device_number
        if size:
            params['sizeGb'] = size
        else:
            raise NTTMCPAPIException('size cannot be None')
        if speed:
            params['speed'] = speed
        else:
            raise NTTMCPAPIException('speed cannot be None')
        if speed == 'PROVISIONEDIOPS' and iops:
            params['iops'] = iops

        url = self.base_url + 'server/addDisk'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def change_iops(self, disk_id=None, disk_iops=None):
        """
        Change the IOPS count for a disk
        """
        params = {}
        if not disk_id:
            raise NTTMCPAPIException('No disk ID supplied')
        if not disk_iops:
            raise NTTMCPAPIException('No disk IOPS count supplied')

        params['id'] = disk_id
        params['iops'] = disk_iops

        url = self.base_url + 'server/changeDiskIops'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def expand_disk(self, server_id=None, disk_id=None, disk_size=None):
        """
        Expand an existing disk size
        """
        params = {}
        if server_id:
            params['id'] = server_id
        else:
            raise NTTMCPAPIException('No server ID supplied')
        if disk_id:
            params['id'] = disk_id
        else:
            raise NTTMCPAPIException('No disk ID supplied')
        if disk_size:
            params['newSizeGb'] = disk_size
        else:
            raise NTTMCPAPIException('No disk size supplied')

        url = self.base_url + 'server/expandDisk'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def update_disk_speed(self, disk_id=None, speed=None, iops=None):
        """
        Modify the speed of an existing disk
        """
        params = {}
        if disk_id is None:
            raise NTTMCPAPIException('disk_id cannot be None')
        if speed is None:
            raise NTTMCPAPIException('speed cannot be None')

        params['id'] = disk_id
        params['speed'] = speed
        if iops is not None and type(iops) is int:
            params['iops'] = iops

        url = self.base_url + 'server/changeDiskSpeed'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def update_disk_iops(self, disk_id=None, iops=None):
        """
        For disks of type PROVISIONEDIOPS, update and IOPS allocated to the disk
        """
        params = {}
        if disk_id is None:
            raise NTTMCPAPIException('disk_id cannot be None')
        if iops is None or type(iops) is not int:
            raise NTTMCPAPIException('iops cannot be None and must be an integer')

        params['id'] = disk_id
        params['iops'] = iops

        url = self.base_url + 'server/changeDiskIops'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def remove_disk(self, disk_id=None):
        """
        Remove a disk from a VM
        """
        params = {}
        if disk_id is None:
            raise NTTMCPAPIException('disk_id cannot be None')

        params['id'] = disk_id

        url = self.base_url + 'server/removeDisk'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def add_controller(self, server_id=None, controller_type=None, adapter_type=None, controller_number=None):
        """
        Add a new disk controller to an existing VM
        """
        params = {}
        if server_id is None:
            raise NTTMCPAPIException('The server ID cannot be None')
        if controller_type is None:
            raise NTTMCPAPIException('The controller type cannot be None')
        if adapter_type is None:
            raise NTTMCPAPIException('The controller adapter type cannot be None')
        if controller_number is not None and type(controller_number) is int:
            params['busNumber'] = controller_number

        params['serverId'] = server_id
        params['adapterType'] = adapter_type


        url = self.base_url + 'server/addScsiController'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def remove_controller(self, controller_id=None):
        """
        Remove a disk controller from an existing VM
        """
        params = {}
        if controller_id is None:
            raise NTTMCPAPIException('The controller ID cannot be None')

        params['id'] = controller_id

        url = self.base_url + 'server/removeScsiController'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def add_nic(self, server_id=None, vlan_id=None, ipv4_address=None, nic_type='VMXNET3', connected=True):
        """
        Add a new NIC to an existing VM - Note the new NIC must be in a new VLAN
        """
        params = {}
        params['nic'] = {}
        if server_id is None:
            raise NTTMCPAPIException('The server ID cannot be None')
        if vlan_id is None and ipv4_address is None:
            raise NTTMCPAPIException('A valid VLAN ID or IPv4 address is required')

        params['serverId'] = server_id
        if ipv4_address:
            params['nic']['privateIpv4'] = ipv4_address
        else:
            params['nic']['vlanId'] = vlan_id
        params['nic']['networkAdapter'] = nic_type
        params['nic']['connected'] = connected

        url = self.base_url + 'server/addNic'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def remove_nic(self, nic_id=None):
        """
        Remove a NIC from an existing VM
        """
        params = {}
        if nic_id is None:
            raise NTTMCPAPIException('The NIC ID cannot be None')

        params['id'] = nic_id

        url = self.base_url + 'server/removeNic'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def change_nic_type(self, nic_id=None, nic_type=None):
        """
        Change the device type of a NIC
        """
        params = {}
        if nic_id is None or nic_type is None:
            raise NTTMCPAPIException('The NIC ID and type cannot be None')

        params['nicId'] = nic_id
        params['networkAdapter'] = nic_type

        url = self.base_url + 'server/changeNetworkAdapter'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def exchange_nic(self, nic_1_id=None, nic_2_id=None):
        """
        Swap VLANs between two existing NICs on a VM
        """
        params = {}
        if nic_1_id is None or nic_2_id is None:
            raise NTTMCPAPIException('The NIC IDs cannot be None')

        params['nicId1'] = nic_1_id
        params['nicId2'] = nic_2_id

        url = self.base_url + 'server/exchangeNicVlans'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')

    def list_snat_exclusion(self, network_domain_id=None, snat_id=None, network=None, prefix=None):
        """
        Return a list of SNAT exclusions
        """
        params = {}
        return_data = []
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid value Network Domain ID is required')
        params['networkDomainId'] = network_domain_id
        if snat_id:
            params['id'] = snat_id
        if network:
            params['destinationIpv4NetworkAddress'] = network

        url = self.base_url + 'network/snatExclusion'

        response = self.api_get_call(url, params)
        try:
            if response != None:
                snats = response.json().get('snatExclusion')
                if network:
                    for snat in snats:
                        if snat.get('id') == snat_id:
                            return_data.append(snat)
                        elif all([network, prefix]):
                            if snat.get('destinationIpv4NetworkAddress') == network and snat.get('destinationIpv4PrefixSize') == prefix:
                                return_data.append(snat)
                        else:
                            if snat.get('destinationIpv4NetworkAddress') == network:
                                return_data.append(snat)
                    return return_data
                return snats
            else:
                raise NTTMCPAPIException('No response from the API')
        except Exception as e:
            raise NTTMCPAPIException('Could not decode the response - {0}'.format(e))


    def get_snat_exclusion(self, snat_id):
        """
        Get a specific SNAT exclusion

        :arg snat_id: The UUID of the SNAT Exclusion
        :returns: List of SNAT Exclusions
        """
        params = {}
        if snat_id is None:
            raise NTTMCPAPIException('The SNAT Exclusion ID is required')

        url = self.base_url + 'network/snatExclusion/{0}'.format(snat_id)

        response = self.api_get_call(url, params)
        try:
            return response.json()
        except KeyError:
            return {}


    def create_snat_exclusion(self, network_domain_id=None, description=None, network=None, prefix=None):
        """
        Create a SNAT exclusion

        :kw network_domain_id: The UUID of the Network Domain
        :kw description: The description of the SNAT exclusion
        :kw network: The destination network for the SNAT exclusion
        :kw prefix: The prefix for the destination network
        :returns: Key/Value pair {'name': 'snatExclusionId', 'value': 'some_uuid'}
        """
        params = {}
        if network_domain_id is None or network is None or prefix is None:
            raise NTTMCPAPIException('A valid value is required for network_domain, network and prefix')

        params['networkDomainId'] = network_domain_id
        if description:
            params['description'] = description
        params['destinationIpv4NetworkAddress'] = network
        params['destinationIpv4PrefixSize'] = prefix

        url = self.base_url + 'network/addSnatExclusion'

        response = self.api_post_call(url, params)
        try:
            return response.json()['info'][0]['value']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create firewall rule request was accepted')


    def remove_snat_exclusion(self, snat_id):
        """
        Remove a SNAT exclusion

        :arg snat_id: The UUID of the SNAT Exclusion
        :returns: {'operation': 'some_operation', responseCode': 'OK', 'message': 'some_message'}
        """
        params = {}
        if snat_id is None:
            raise NTTMCPAPIException('A SNAT exclusion ID is required')
        params['id'] = snat_id

        url = self.base_url + 'network/removeSnatExclusion'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def restore_snat_exclusion(self, network_domain_id):
        """
        Restore SNAT exclusions to the defaultPersistenceProfile

        :arg network_domain_id: The UUID of the Cloud Network Domain
        :returns: {'operation': 'some_operation', responseCode': 'OK', 'message': 'some_message'}
        """
        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain is required')

        params['networkDomainId'] = network_domain_id

        url = self.base_url + 'network/restoreSnatExclusions'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def list_static_routes(self, network_domain_id=None, name=None, version=None, network=None, prefix=None, next_hop=None):
        """
        List static routes
        """
        params = {}
        return_data = []
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid value Network Domain ID is required')

        params['networkDomainId'] = network_domain_id
        if version:
            params['ipVersion'] = version
        if name:
            params['name'] = name

        url = self.base_url + 'network/staticRoute'

        response = self.api_get_call(url, params)
        if response != None:
            routes = response.json().get('staticRoute')
            if network is not None or next_hop:
                for route in routes:
                    if route.get('name') == name:
                        return_data.append(route)
                    elif all([network, prefix, next_hop]):
                        if (route.get('destinationNetworkAddress') == network
                                and route.get('destinationPrefixSize') == prefix
                                and route.get('nextHopAddress') == next_hop
                           ):
                            return_data.append(route)
                    elif all([network, prefix]):
                        if route.get('destinationNetworkAddress') == network and route.get('destinationPrefixSize') == prefix:
                            return_data.append(route)
                    elif all([network, next_hop]):
                        if route.get('destinationNetworkAddress') == network and route.get('nextHopAddress') == next_hop:
                            return_data.append(route)
                    elif network:
                        if route.get('destinationNetworkAddress') == network:
                            return_data.append(route)
                    elif next_hop:
                        if route.get('nextHopAddress') == next_hop:
                            return_data.append(route)
            else:
                return_data = routes
            return return_data
        else:
            raise NTTMCPAPIException('No response from the API')


    def create_static_route(self, network_domain_id=None, name=None, description=None,
                            version=None, network=None, prefix=None, next_hop=None):
        """
        Create a static route
        """
        params = {}
        if not all([network_domain_id, name, version, network, prefix, next_hop]):
            raise NTTMCPAPIException('A valid value is required for network_domain, name, version, network, prefix and next_hop')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['ipVersion'] = version
        params['destinationNetworkAddress'] = network
        params['destinationPrefixSize'] = prefix
        params['nextHopAddress'] = next_hop

        url = self.base_url + 'network/createStaticRoute'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')

    def remove_static_route(self, static_route_id):
        """
        Remove a static route
        """
        params = {}
        if static_route_id is None:
            raise NTTMCPAPIException('A Static Route ID is required')
        params['id'] = static_route_id

        url = self.base_url + 'network/deleteStaticRoute'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def restore_static_routes(self, network_domain_id):
        """
        Restore static routes to defaults
        """
        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain is required')

        params['networkDomainId'] = network_domain_id

        url = self.base_url + 'network/restoreStaticRoutes'

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_geo(self, geo_id=None, geo_name=None, is_home=False):
        """
        Return the geo object for a given UUID or name
        """
        params = {}
        if geo_id:
            params['id'] = geo_id
        if geo_name:
            params['name'] = geo_name
        params['isHome'] = is_home

        url = ('https://%s/caas/%s/%s/infrastructure/geographicRegion' %
               (self.home_geo, API_VERSION, self.org_id))

        response = self.api_get_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_dc(self, dc_id=None):
        """
        Return a MCP/datacenter object for a given UUID
        """
        params = {}
        if dc_id:
            params['id'] = dc_id

        url = self.base_url + 'infrastructure/datacenter'

        response = self.api_get_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_os(self, os_id=None, os_name=None, os_family=None):
        """
        Return an OS object for a given UUID, name or family
        """
        params = {}
        if os_id:
            if '*' in os_id:
                params['id.LIKE'] = os_id
            else:
                params['id'] = os_id
        if os_name:
            if '*' in os_name:
                params['name.LIKE'] = os_name
            else:
                params['name'] = os_name
        if os_family:
            params['family'] = os_family

        url = self.base_url + 'infrastructure/operatingSystem'

        response = self.api_get_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')

    def list_image(self, datacenter_id=None, image_id=None, image_name=None, os_family=None):
        """
        Return an array of images based on a datacenter, UUID, name or family
        """
        params = {}
        if image_id:
            if '*' in image_id:
                params['id.LIKE'] = image_id
            else:
                params['id'] = image_id
        if image_name:
            if '*' in image_name:
                params['name.LIKE'] = image_name
            else:
                params['name'] = image_name
        if os_family:
            params['family'] = os_family
        if datacenter_id:
            params['datacenterId'] = datacenter_id

        url = self.base_url + 'image/osImage'

        response = self.api_get_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_customer_image(self, image_id):
        """
        Return a customer imported image

        :arg image_id: The UUID of the image
        :returns: the customer image object
        """
        url = self.base_url + 'image/customerImage/%s' % image_id

        response = self.api_get_call(url)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def list_customer_image(self, datacenter_id=None, image_id=None, image_name=None, os_family=None):
        """
        List customer images based on the supplied filter criteria

        arg: datacenter_id: The UUID of the MCP
        arg: image_id: The UUID of an existing customer image
        arg: image_name: The name of an existing customer image
        arg: os_family: The operating system family type
        returns: A list of customer image objects
        """
        params = {}
        if image_id:
            if '*' in image_id:
                params['id.LIKE'] = image_id
            else:
                params['id'] = image_id
        if image_name:
            if '*' in image_name:
                params['name.LIKE'] = image_name
            else:
                params['name'] = image_name
        if os_family:
            params['family'] = os_family
        if datacenter_id:
            params['datacenterId'] = datacenter_id

        url = self.base_url + 'image/customerImage'

        response = self.api_get_call(url, params)
        if response != None:
            try:
                return response.json().get('customerImage')
            except AttributeError:
                raise NTTMCPAPIException('Error with the API response')
        else:
            raise NTTMCPAPIException('No response from the API')


    def import_customer_image(self, datacenter_id, ovf_package, image_name, description, guest_customization):
        """
        Import a customer image

        :arg datacenter: The datacenter ID e.g. NA9
        :arg ovf_package: The filename of the OVF manifest file on the FTPS server
        :arg image_name: The name to be assigned to the imported image
        :arg description: The image description in Cloud Control
        :arg guest_customization: Boolean to enable/disable Guest OS Customization
        :returns: the customer image object
        """
        url = self.base_url + 'image/importImage'
        params = {}

        if datacenter_id is None:
            raise NTTMCPAPIException('datacenter_id cannot be None')
        else:
            params['datacenterId'] = datacenter_id
        if ovf_package is None:
            raise NTTMCPAPIException('ovf_package cannot be None')
        else:
            params['ovfPackage'] = ovf_package
        if image_name is None:
            raise NTTMCPAPIException('image_name cannot be None')
        else:
            params['name'] = image_name
        if description:
            params['description'] = description
        if guest_customization is None:
            raise NTTMCPAPIException('guest_customization cannot be None')
        else:
            params['guestOsCustomization'] = guest_customization

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def delete_customer_image(self, image_id):
        """
        Delete a customer image

        :arg image_id: The GUID to be assigned to the customer image
        :returns: the customer image object
        """
        url = self.base_url + 'image/deleteCustomerImage'
        params = {}

        if image_id is None:
            raise NTTMCPAPIException('image_id cannot be None')
        else:
            params['id'] = image_id

        response = self.api_post_call(url, params)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def list_public_ipv4(self, network_domain_id):
        """
        Return a list all public IPv4 addresses for the given Cloud Network Domain

        :arg network_domain_id: Cloud Network Domain UUID
        :returns: Array of UUIDs of found public IPv4 block or empty array
        """
        url = self.base_url + 'network/publicIpBlock'

        params = {'networkDomainId': network_domain_id}
        response = self.api_get_call(url, params)
        try:
            return response.json()['publicIpBlock']
        except KeyError:
            return []


    def get_public_ipv4(self, public_ipv4_block_id):
        """
        Return a specific public IPv4 block object

        :arg public_ipv4_block_id: Public IPv4 block UUID
        :returns: UUID of the public IPv4 block
        """
        url = self.base_url + 'network/publicIpBlock/%s' % (public_ipv4_block_id)

        response = self.api_get_call(url)
        if response != None:
            if response.json().get('responseCode') == 'RESOURCE_NOT_FOUND':
                return []
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_public_ipv4_by_ip(self, network_domain_id, public_ipv4):
        """
        Return a specific public IPv4 block object

        :arg network_domain_id: Cloud Network Domain UUID
        :arg public_ipv4: A public IPv4 address
        :returns: The public IPv4 block dict
        """
        ip_list = []
        ip_to_int = lambda ip_address: struct.unpack('!I', socket.inet_aton(ip_address))[0]
        public_ipv4_int = ip_to_int(public_ipv4)
        try:
            public_ip_blocks = self.list_public_ipv4(network_domain_id)
            for public_block in public_ip_blocks:
                ip_list.append(ip_to_int(public_block['baseIp']))
                for i in range(public_block['size']):
                    ip_list.append(ip_to_int(public_block['baseIp']) + i)
                if public_ipv4_int in ip_list:
                    return public_block
            return None
        except Exception as e:
            raise NTTMCPAPIException('{0}'.format(e))


    def get_next_public_ipv4(self, network_domain_id):
        """
        Return the next available public IPv4 address
        If no more IPv4 addresses are available in the current allocated /30
        blocks, allocate a new /30 block
        """
        return_data = {}
        return_data['changed'] = False
        ip_to_int = lambda ip_address: struct.unpack('!I', socket.inet_aton(ip_address))[0]
        int_to_ip = lambda i: socket.inet_ntoa(struct.pack('!I', i))
        nat_public_ip_list = []
        try:
            public_ip_blocks = self.list_public_ipv4(network_domain_id)
            nats = self.list_nat_rule(network_domain_id)
            for nat in nats:
                nat_public_ip_list.append(nat['externalIp'])
            for public_block in public_ip_blocks:
                ip1 = public_block['baseIp']
                ip2 = int_to_ip(ip_to_int(ip1) + 1)
                if ip1 not in nat_public_ip_list:
                    return_data['ipAddress'] = ip1
                    return return_data
                elif ip2 not in nat_public_ip_list:
                    return_data['ipAddress'] = ip2
                    return return_data

            # If you're here that means there are no existing blocks and we need to allocate a new one
            return_data['changed'] = True
            block_id = self.add_public_ipv4(network_domain_id)
            return_data['ipAddress'] = self.get_public_ipv4(block_id)['baseIp']
            return return_data
        except Exception as e:
            raise NTTMCPAPIException('{0}'.format(e))


    def add_public_ipv4(self, network_domain_id):
        """
        Add a new /30 public IPv4 block to a Cloud Network Domain

        :arg network_domain_id: Cloud Network Domain UUID
        :returns: UUID of the new public IPv4 block
        """
        params = {'networkDomainId': network_domain_id}

        url = self.base_url + 'network/addPublicIpBlock'
        response = self.api_post_call(url, params)
        try:
            return response.json()['info'][0]['value']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the add public ipv4 block request was accepted')


    def remove_public_ipv4(self, public_ipv4_block_id):
        """
        Remove a public IPv4 block

        :arg public_ipv4_block_id: Public IPv4 block UUID
        :returns: string (API message)
        """
        params = {'id': public_ipv4_block_id}

        url = self.base_url + 'network/removePublicIpBlock'
        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove public ipv4 block request was accepted')


    def check_public_block_in_use(self, network_domain_id, base_public_ipv4):
        """
        Check if a public ipv4 block is in use

        :arg network_domain_id: The UUID of the CND
        :arg base_public_ipv4: The base IPv4 address of the public block
        :returns: True or False
        """
        nat_public_ip_list = []
        ip1 = base_public_ipv4
        ip2 = INT_TO_IP(IP_TO_INT(ip1) + 1)
        try:
            nats = self.list_nat_rule(network_domain_id)
            for nat in nats:
                nat_public_ip_list.append(nat.get('externalIp'))
            if ip1 not in nat_public_ip_list and ip2 not in nat_public_ip_list:
                return False
            return True
        except (KeyError, IndexError, NTTMCPAPIException) as e:
            raise NTTMCPAPIException('{0}'.format(e))


    def list_reserved_ip(self, vlan_id=None, datacenter_id=None, version=4):
        """
        Return an array of reserved IPv4 or IPv6 addresses

        :kw vlan_id: VLAN UUID
        :kw datacenter_id: datacenter ID (e.g. NA9)
        :kw version: IP version (deafult = 4)
        :returns: Array of private IPv4 reservations or empty array
        """
        params = {}
        if vlan_id is None and datacenter_id is None:
            raise NTTMCPAPIException('A vlan or datacenter must be provided')
        if version != 4 and version != 6:
            raise NTTMCPAPIException('Invalid IP version - %d' % version)
        # Prefer VLAN ID over datacenter ID
        if vlan_id:
            params['vlanId'] = vlan_id
        elif datacenter_id:
            params['datacenterId'] = datacenter_id

        url = self.base_url + 'network/reservedPrivateIpv4Address'
        if version == 6:
            url = self.base_url + 'network/reservedIpv6Address'

        response = self.api_get_call(url, params)
        try:
            if version == 4:
                return response.json()['ipv4']
            elif version == 6:
                return response.json()['reservedIpv6Address']
            else:
                raise NTTMCPAPIException('Invalid IP version')
        except (KeyError, NTTMCPAPIException) as e:
            raise NTTMCPAPIException(e)
            #return []


    def reserve_ip(self, vlan_id=None, ip_address=None, description=None, version=4):
        """
        Reserve an IPv4 or IPv6 address - prevents Cloud Control from auto allocating

        :kw vlan_id: VLAN UUID
        :kw ip_address: The IP address to reserve
        :kw description: The description of the reserve IPv4 address
        :kw version: IP version (deafult = 4)
        :returns: the returned confirmed IPv4 address
        """
        params = {}
        if vlan_id is None or ip_address is None:
            raise NTTMCPAPIException('A vlan and IPv4 address must be provided')
        if version != 4 and version != 6:
            raise NTTMCPAPIException('Invalid IP version - {0}'.format(version))
        params['vlanId'] = vlan_id
        params['ipAddress'] = ip_address
        if description:
            params['description'] = description

        url = self.base_url + 'network/reservePrivateIpv4Address'
        if version == 6:
            url = self.base_url + 'network/reserveIpv6Address'

        response = self.api_post_call(url, params)
        try:
            if ip_addr(unicode(response.json().get('info')[0].get('value'))) == ip_addr(unicode(ip_address)):
                return response.json().get('info')[0].get('value')
            else:
                raise NTTMCPAPIException('Could not reserve the private IPv{0} address: {1}'.format(version, response))
        except (KeyError, IndexError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the reserve private ipv{0} address request was accepted'.format(version))


    def unreserve_ip(self, vlan_id=None, ip_address=None, version=4):
        """
        Unreserve an IPv4 or IPv6 address

        :arg vlan_id: VLAN UUID
        :arg ipv_address: The IP address to reserve
        :returns: string (API message)
        """
        params = {}
        if vlan_id is None or ip_address is None:
            raise NTTMCPAPIException('A vlan and IPv4 address must be '
                                     'provided')
        if version != 4 and version != 6:
            raise NTTMCPAPIException('Invalid IP version - {0}'.format(version))
        params['vlanId'] = vlan_id
        params['ipAddress'] = ip_address

        url = self.base_url + 'network/unreservePrivateIpv4Address'
        if version == 6:
            url = self.base_url + 'network/unreserveIpv6Address'

        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the unreserving of the private ipv{0} address request was accepted'.format(version))


    def list_nat_rule(self, network_domain_id):
        """
        Return an array of NAT rules for a Cloud Network Domain

        :arg network_domain_id: Cloud Network Domain UUID
        :returns: Array of NATs
        """
        url = self.base_url + 'network/natRule'

        params = {'networkDomainId': network_domain_id}
        response = self.api_get_call(url, params)
        try:
            return response.json()['natRule']
        except KeyError:
            return []


    def create_nat_rule(self, network_domain_id=None, internal_ip=None, external_ip=None):
        """
        Create a new NAT rule

        :arg network_domain_id: Cloud Network Domain UUID
        :arg ip_address: The IP address to reserve
        :arg description: The description of the reserve IPv4 address
        :arg version: IP version (deafult = 4)
        :returns: the returned confirmed IPv4 address
        """
        params = {}
        if internal_ip is None or external_ip is None:
            raise NTTMCPAPIException('A valid internal and external IP address must be provided')
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain is required')
        params['networkDomainId'] = network_domain_id
        params['internalIp'] = internal_ip
        params['externalIp'] = external_ip

        url = self.base_url + 'network/createNatRule'

        response = self.api_post_call(url, params)
        try:
            return response.json()['info'][0]['value']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the create NAT rule request was accepted')
        except IndexError:
            raise NTTMCPAPIException('Could not confirm that the create NAT rule request was accepted')


    def get_nat_rule(self, nat_rule_id):
        """
        Return a specific NAT rule by UUID

        :arg nat_rule_id: NAT rule UUID
        :returns: The NAT rule object
        """
        url = self.base_url + 'network/natRule/{0}}'.format(nat_rule_id)

        response = self.api_get_call(url)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_nat_by_private_ip(self, network_domain_id, private_ip):
        """
        Return a specific NAT rule based on the private IPv4 address

        :arg network_domain_id: The UUID of the CND:
        :arg private_ip: The private IPv4 address to search by
        :returns: The NAT rule object
        """
        try:
            nat_rules = self.list_nat_rule(network_domain_id)
            for nat_rule  in nat_rules:
                if nat_rule['internalIp'] == private_ip:
                    return nat_rule
            return None
        except Exception as e:
            raise NTTMCPAPIException('{0}'.format(e))

    def get_nat_by_public_ip(self, network_domain_id, public_ip):
        """
        Return a specific NAT rule based on the public IPv4 address

        :arg network_domain_id: The UUID of the CND:
        :arg public_ip: The public IPv4 address to search by
        :returns: The NAT rule object
        """
        try:
            nat_rules = self.list_nat_rule(network_domain_id)
            for nat_rule  in nat_rules:
                if nat_rule['externalIp'] == public_ip:
                    return nat_rule
            return None
        except Exception as e:
            raise NTTMCPAPIException('{0}'.format(e))


    def remove_nat_rule(self, nat_rule_id):
        """
        Remove a NAT rules

        :arg nat_rule_id: NAT rule UUID
        :returns: string (API message)
        """
        params = {'id': nat_rule_id}

        url = self.base_url + 'network/deleteNatRule'
        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove NAT rule request was accepted')


    def list_port_list(self, network_domain_id):
        """
        Return an array of port lists for a specified Cloud Network Domains

        :arg network_domain_id: Cloud Network Domain UUID
        :returns: Array of Port Lists
        """
        url = self.base_url + 'network/portList'

        params = {'networkDomainId': network_domain_id}
        response = self.api_get_call(url, params)
        try:
            return response.json()['portList']
        except KeyError:
            return []


    def get_port_list(self, network_domain_id, port_list_id):
        """
        Return a port list based on UUIDs

        :arg network_domain_id: Cloud Network Domain UUID
        :arg port_list_id: The UUID of a Port List
        :returns: Port List
        """
        url = self.base_url + 'network/portList/%s' % port_list_id

        response = self.api_get_call(url)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_port_list_by_name(self, network_domain_id, name):
        """
        Return a port list based on a specified name

        :arg network_domain_id: Cloud Network Domain UUID
        :arg name: The name of a Port List
        :returns: Port List or None
        """
        url = self.base_url + 'network/portList'

        params = {'networkDomainId': network_domain_id}
        response = self.api_get_call(url, params)
        try:
            port_lists = response.json()['portList']
            port_list = [x for x in port_lists if x.get('name') == name]
            return port_list[0]
        except (KeyError, IndexError):
            return None

    def create_port_list(self, network_domain_id, name, description, ports, child_port_lists):
        """
        Create a port list

        :arg network_domain_id: Cloud Network Domain UUID
        :arg name: The name of a Port List
        :arg description: The description of the port list
        :arg ports: An array of beginning and end ports
        :arg child_port_list: An array of port list UUIDs
        :returns: Port List UUID
        """
        if network_domain_id is None or name is None or (ports is None and child_port_lists is None):
            raise NTTMCPAPIException('A valid Network Domain, Name and Beginning Port is required')

        params = self.port_list_args_to_dict(True,
                                             network_domain_id,
                                             None,
                                             name,
                                             description,
                                             ports,
                                             None,
                                             child_port_lists,
                                             None
                                            )
        url = self.base_url + 'network/createPortList'

        response = self.api_post_call(url, params)
        try:
            return response.json()['info'][0]['value']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create Port List request was accepted')


    def update_port_list(self, network_domain_id, port_list_id, description, ports, ports_nil, child_port_lists, child_port_lists_nil):
        """
        Update an existing port list

        :arg network_domain_id: The UUID of the Cloud Network Domain
        :arg port_list_id: The UUID of a Port List
        :arg description: The description of the port list
        :arg ports: An array of beginning and end ports
        :arg ports_nil: Boolean to denote whether to delete all ports
        :arg child_port_lists: An array of port list UUIDs
        :arg child_port_lists_nil: Boolean to denote whether to delete all child Port Lists
        :returns: Port List UUID
        """
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain ID is required')
        if port_list_id is None:
            raise NTTMCPAPIException('A valid Port List ID is required')

        params = self.port_list_args_to_dict(False,
                                             network_domain_id,
                                             port_list_id,
                                             None,
                                             description,
                                             ports,
                                             ports_nil,
                                             child_port_lists,
                                             child_port_lists_nil
                                            )
        params.pop('name')
        url = self.base_url + 'network/editPortList'

        response = self.api_post_call(url, params)
        try:
            return response.json()['responseCode']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update Port List request was accepted')


    def port_list_args_to_dict(self, create, network_domain_id, port_list_id, name, description,
                               ports, ports_nil, child_port_list, child_port_list_nil):
        """
        Convert a list of port list args to a dict
        """
        child_port_list_id = []
        params = {}
        params['port'] = []
        params['name'] = name

        if not create:
            params['id'] = port_list_id
        else:
            params['networkDomainId'] = network_domain_id

        if child_port_list_nil:
            child_port_list_id.append({'nil': True})
        elif child_port_list:
            if network_domain_id is None:
                raise NTTMCPAPIException('A valid Network Domain is required')
            for port_list_name in child_port_list:
                try:
                    result = self.get_port_list_by_name(network_domain_id, port_list_name)
                    child_port_list_id.append(result.get('id'))
                except (KeyError, IndexError, NTTMCPAPIException):
                    raise NTTMCPAPIException('Could not find child port lists')

        if ports_nil:
            params['port'].append({'nil': True})
        else:
            for port in ports:
                new_port_group = {}
                try:
                    new_port_group['begin'] = port['port_begin']
                    if 'port_end' in port:
                        if port['port_end'] > port['port_begin']:
                            new_port_group['end'] = port['port_end']
                        else:
                            raise NTTMCPAPIException('End port must be greater than the beginning port')
                    params['port'].append(new_port_group)
                except KeyError:
                    raise NTTMCPAPIException('Port groups must have a beginning port')

        if description:
            params['description'] = description

        if child_port_list_id:
            params['childPortListId'] = child_port_list_id

        return params


    def remove_port_list(self, port_list_id):
        """
        Remove a port list - Note port list must not be currently used in a firewall rule

        :arg port_list_id: Port List UUID
        :returns: string (API message)
        """
        params = {'id': port_list_id}

        url = self.base_url + 'network/deletePortList'
        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove Port List request was accepted')


    def list_ip_list(self, network_domain_id, version):
        """
        Return an array of IP address lists

        :arg network_domain_id: Cloud Network Domain UUID
        :arg version: IP version
        :returns: Array of IP Address Lists
        """
        url = self.base_url + 'network/ipAddressList'

        params = {'networkDomainId': network_domain_id}
        if version:
            params['ipVersion'] = version

        response = self.api_get_call(url, params)
        try:
            return response.json()['ipAddressList']
        except KeyError:
            return []


    def get_ip_list(self, network_domain_id, ip_address_list_id):
        """
        Return a specific IP address list based on a UUID
        :arg network_domain_id: Cloud Network Domain UUID
        :arg port_list_id: The UUID of a IP Address List
        :returns: IP Address List
        """
        url = self.base_url + 'network/ipAddressList/%s' % ip_address_list_id

        response = self.api_get_call(url)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_ip_list_by_name(self, network_domain_id, name, version):
        """
        Return a specific IP address list for the specified name

        :arg network_domain_id: Cloud Network Domain UUID
        :arg name: The name of a IP Address List
        :returns: IP Address List
        """
        url = self.base_url + 'network/ipAddressList'

        params = {'networkDomainId': network_domain_id}
        if version:
            params['ipVersion'] = version
        response = self.api_get_call(url, params)
        try:
            ip_address_lists = response.json()['ipAddressList']
            ip_address_list_exists = [x for x in ip_address_lists if x.get('name') == name]
            return ip_address_list_exists[0]
        except KeyError:
            return None
        except IndexError:
            return None


    def create_ip_list(self, network_domain_id, name, description, ip_addresses, child_ip_lists, version):
        """
        :arg network_domain_id: Cloud Network Domain UUID
        :arg name: The name of a IP Address List
        :arg description: The description of the IP Address list
        :arg ip_addresses: An array of beginning and end ports
        :arg child_ip_lists: An array of IP Address list UUIDs
        :arg version: IP version
        :returns: IP Address List UUID
        """
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain ID is required')
        if name is None:
            raise NTTMCPAPIException('A valid IP address list name is required')

        params = self.ip_list_args_to_dict(True,
                                           network_domain_id,
                                           None,
                                           name,
                                           description,
                                           ip_addresses,
                                           False,
                                           child_ip_lists,
                                           False,
                                           version
                                          )

        url = self.base_url + 'network/createIpAddressList'
        response = self.api_post_call(url, params)
        try:
            return response.json()['info'][0]['value']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create IP Address List request was accepted')


    def update_ip_list(self, network_domain_id, ip_address_list_id, description, ip_addresses, ip_addresses_nil,
                       child_ip_lists, child_ip_lists_nil):
        """
        Update an existing IP address list

        :arg network_domain_id: The UUID of the Cloud Network Domain
        :arg ip_address_list_id: The UUID of a IP Address List
        :arg description: The description of the IP Address list
        :arg ip_addresses: An array of beginning and end ip addresses
        :arg ip_addresses_nil: Boolean to denote whether to delete all ip addresses
        :arg child_ip_lists: An array of IP Address list UUIDs
        :arg child_ip_lists_nil: Boolean to denote whether to delete all child IP Address Lists
        :returns: Port List UUID
        """
        if network_domain_id is None:
            raise NTTMCPAPIException('A valid Network Domain ID is required')
        if ip_address_list_id is None:
            raise NTTMCPAPIException('A valid IP Address List ID is required')

        params = self.ip_list_args_to_dict(False,
                                           network_domain_id,
                                           ip_address_list_id,
                                           None,
                                           description,
                                           ip_addresses,
                                           ip_addresses_nil,
                                           child_ip_lists,
                                           child_ip_lists_nil,
                                           None
                                          )
        params.pop('name')
        params.pop('ipVersion')

        url = self.base_url + 'network/editIpAddressList'

        response = self.api_post_call(url, params)
        try:
            return response.json()['responseCode']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update IP Address List request was accepted')


    def ip_list_args_to_dict(self, create, network_domain_id, ip_address_list_id, name, description, ip_addresses,
                             ip_addresses_nil, child_ip_lists, child_ip_lists_nil, version):
        """
        Convert a list of IP address list arguments to a dict
        :arg network_domain_id: The UUID of the Cloud Network Domain
        :arg ip_address_list_id: The UUID of a IP Address List
        :arg description: The description of the IP Address list
        :arg ip_addresses: An array of beginning and end ip addresses
        :arg ip_addresses_nil: Boolean to denote whether to delete all ip addresses
        :arg child_ip_lists: An array of IP Address list UUIDs
        :arg child_ip_lists_nil: Boolean to denote whether to delete all child IP Address Lists
        :returns: Port List UUID
        """
        child_ip_list_id = []
        params = {}
        params['ipAddress'] = []
        params['name'] = name
        params['ipVersion'] = version

        if not create:
            params['id'] = ip_address_list_id
        else:
            params['networkDomainId'] = network_domain_id

        if child_ip_lists_nil:
            child_ip_list_id.append({'nil': True})
        elif child_ip_lists:
            if network_domain_id is None:
                raise NTTMCPAPIException('A valid Network Domain is required')
            for child_ip_list in child_ip_lists:
                try:
                    result = self.get_ip_list_by_name(network_domain_id, child_ip_list, version)
                    child_ip_list_id.append(result.get('id'))
                except Exception:
                    raise NTTMCPAPIException('Could not find child IP Address lists')

        if ip_addresses_nil:
            params['ipAddress'].append({'nil': True})
        else:
            for ip_address in ip_addresses:
                new_ip_group = {}
                try:
                    new_ip_group['begin'] = ip_address.get('begin')
                    if 'end' in ip_address:
                        new_ip_group['end'] = ip_address.get('end')
                    elif 'prefix' in ip_address:
                        new_ip_group['prefixSize'] = ip_address.get('prefix')
                    params['ipAddress'].append(new_ip_group)
                except KeyError:
                    raise NTTMCPAPIException('IP Addresses must have a beginning IP Address')


        if description:
            params['description'] = description

        if child_ip_list_id:
            params['childIpAddressListId'] = child_ip_list_id

        return params


    def remove_ip_list(self, ip_address_list_id):
        """
        Remove an IP address list

        :arg ip_address_list_id: IP Address List UUID
        :returns: string (API message)
        """
        params = {'id': ip_address_list_id}

        url = self.base_url + 'network/deleteIpAddressList'
        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove IP Address List request was accepted')


    def list_fw_rules(self, network_domain_id,):
        """
        Return an array of firewall rules for the specified Cloud Network Domain

        :arg network_domain_id: Cloud Network Domain UUID
        :returns: Array of firewall rules
        """
        url = self.base_url + 'network/firewallRule'

        params = {'networkDomainId': network_domain_id}

        response = self.api_get_call(url, params)
        try:
            return response.json()['firewallRule']
        except KeyError:
            return []


    def get_fw_rule(self, network_domain_id, fw_rule_id):
        """
        Return a specific firewall rule based on a UUID

        :arg network_domain_id: Cloud Network Domain UUID
        :arg fw_rule_id: The UUID of an ACL rule
        :returns: firewall rule
        """
        url = self.base_url + 'network/firewallRule/{0}'.format(fw_rule_id)

        response = self.api_get_call(url)
        if response != None:
            return response.json()
        else:
            raise NTTMCPAPIException('No response from the API')


    def get_fw_rule_by_name(self, network_domain_id, name):
        """
        :arg network_domain_id: Cloud Network Domain UUID
        :arg name: The name of a firewall rule
        :arg version: the IP version ([IPV4, IPv6])
        :returns: firewall rule
        """
        url = self.base_url + 'network/firewallRule'

        params = {'networkDomainId': network_domain_id}
        response = self.api_get_call(url, params)
        try:
            fw_rules = response.json()['firewallRule']
            fw_rule_exists = [x for x in fw_rules if x.get('name') == name]
            return fw_rule_exists[0]
        except KeyError:
            return None
        except IndexError:
            return None


    def create_fw_rule(self, fw_rule):
        """
        Create a firewall rule from the specified dict of arguments

        :arg fw_rule: The new Firewall rule dict
        :returns: message
        """
        url = self.base_url + 'network/createFirewallRule'
        fw_src = fw_rule['source']
        fw_dst = fw_rule['destination']

        if fw_rule['networkDomainId'] is None:
            raise NTTMCPAPIException('Network Domain UUID is required')
        if fw_rule['name'] is None:
            raise NTTMCPAPIException('Name is required')
        if 'ip' not in fw_src and 'ipAddressListId' not in fw_src:
            raise NTTMCPAPIException('Source IP or IP Address list is required')
        if 'ip' not in fw_dst and 'ipAddressListId' not in fw_dst:
            raise NTTMCPAPIException('Destination IP or IP Address list is required')
        if 'port' in fw_src:
            if 'begin' not in fw_src['port']:
                raise NTTMCPAPIException('Source Port or Port list is required')
        if 'port' in fw_dst:
            if 'begin' not in fw_dst['port']:
                raise NTTMCPAPIException('Destination Port or Port list is required')

        response = self.api_post_call(url, fw_rule)
        try:
            return response.json()['info'][0]['value']
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create firewall rule request was accepted')


    def fw_args_to_dict(self, create, fw_rule_id, network_domain_id, name, action, version,
                        protocol, src_ip, src_ip_prefix, src_ip_list_id,
                        dst_ip, dst_ip_prefix, dst_ip_list_id, src_port_begin,
                        src_port_end, src_port_list_id, dst_port_begin,
                        dst_port_end, dst_port_list_id, enabled, position,
                        position_to):
        """
        Convert a list of firewall rule arguments to a dict

        :arg create: Boolean as to whether or not to create an ACL
        :arg fw_rule_id: UUID of the firewall rule
        :arg network_domain_id: The UUID of the CND
        :arg action: [ACCEPT_DECISIVELY, DROP]
        :arg protocol: [IP, ICMP, TCP, UDP]
        :arg src_ip: (string) IPv4 or IPv6 address
        :arg src_ip_prefix: (string) IP prefix
        :arg src_ip_list_id: (string) UUID of an IP Address List
        :arg dst_ip: (string) IPv4 or IPv6 address
        :arg dst_ip_prefix: (string) IP prefix
        :arg dst_ip_list_id: (string) UUID of an IP Address List
        :arg src_port_begin: (string) beginning port number for
        :arg src_port_end: (string) end port number for a port range
        :arg src_port_list: (string) UUID of a port list
        :arg dst_port_begin: (string) beginning port number
        :arg dst_port_end: (string) end port number for a port range
        :arg dst_port_list: (string) UUID of a port list
        :arg enabled: (boolean) whether to enable the firewall rule
        :arg position: [FIRST, LAST, BEFORE, AFTER]
        :arg position_to: (string) name of an existing firewall rule
        :returns: Firewall Rule Dictionary
        """
        params = {}
        if create:
            params['placement'] = {}
        if src_ip is not None or src_ip_list_id is not None or src_port_begin is not None or src_port_list_id:
            params['source'] = {}
        if dst_ip is not None or dst_ip_list_id is not None or dst_port_begin is not None or dst_port_list_id:
            params['destination'] = {}

        if not create:
            if fw_rule_id:
                params['id'] = fw_rule_id
        else:
            if network_domain_id:
                params['networkDomainId'] = network_domain_id
            if name:
                params['name'] = name

        if src_ip_list_id:
            params['source']['ipAddressListId'] = src_ip_list_id
        else:
            params['source']['ip'] = {}
            params['source']['ip']['address'] = src_ip
            if src_ip_prefix:
                params['source']['ip']['prefixSize'] = src_ip_prefix
        if dst_ip_list_id:
            params['destination']['ipAddressListId'] = dst_ip_list_id
        else:
            params['destination']['ip'] = {}
            params['destination']['ip']['address'] = dst_ip
            if dst_ip_prefix:
                params['destination']['ip']['prefixSize'] = dst_ip_prefix
        if src_port_list_id:
            params['source']['portListId'] = src_port_list_id
        else:
            if src_port_begin != 'ANY' and src_port_begin:
                params['source']['port'] = {}
                params['source']['port']['begin'] = src_port_begin
                if src_port_end:
                    params['source']['port']['end'] = src_port_end
        if dst_port_list_id:
            params['destination']['portListId'] = dst_port_list_id
        else:
            if dst_port_begin != 'ANY' and dst_port_begin:
                params['destination']['port'] = {}
                params['destination']['port']['begin'] = dst_port_begin
                if dst_port_end:
                    params['destination']['port']['end'] = dst_port_end

        # Configure the defaults
        if create:
            if position is None:
                position = 'LAST'
            if position_to:
                params['placement']['relativeToRule'] = position_to
            params['ipVersion'] = version
            params['placement']['position'] = position

        if action is None:
            action = 'ACCEPT_DECISIVELY'
        if version is None:
            version = 'IPV4'
        if protocol is None:
            protocol = 'TCP'
        if enabled is None:
            enabled = True
        params['enabled'] = enabled
        params['protocol'] = protocol

        params['action'] = action

        return params


    def update_fw_rule(self, fw_rule):
        """
        Update an existing firewall rule

        :arg fw_rule: a Firewall rule dictionary
        :returns: message
        """
        url = self.base_url + 'network/editFirewallRule'

        if fw_rule['id'] is None:
            raise NTTMCPAPIException('Id is required')

        response = self.api_post_call(url, fw_rule)
        try:
            return response.json().get('responseCode')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update firewall rule request was accepted')


    def remove_fw_rule(self, firewall_rule_id):
        """
        Remove a firewall rule

        :arg fw_rule_id: UUID of the firewall rule
        :returns: string (API message)
        """
        params = {'id': firewall_rule_id}

        url = self.base_url + 'network/deleteFirewallRule'
        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove firewall rule request was accepted')


    def list_vip_node(self, network_domain_id=None, name=None, ip_address=None):
        """
        Return a list of Virtual IP nodes

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The node name
        :kw ip_address: the IPv4 or IPv6 address for the node
        :returns: List of Nodes
        """
        params = {}
        version = None
        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain is required')

        params['networkDomainId'] = network_domain_id
        if name:
            params['name'] = name
        if ip_address:
            version = get_ip_version(ip_address)

        # Any supplied name trumps a supplied version and ip_address
        if name:
            params['name'] = name
        elif version is not None and ip_address:
            params['ipv{0}Address'.format(version)] = ip_address

        url = self.base_url + 'networkDomainVip/node'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('node')
        except Exception:
            return []


    def get_vip_node(self, node_id):
        """
        Return a specific Virtual IP node

        :arg node_id: The UUID of a VIP Node
        :return: List of Nodes
        """
        params = {}
        if node_id is None:
            raise NTTMCPAPIException('The Node ID is required')

        url = self.base_url + 'networkDomainVip/node/{0}'.format(node_id)

        response = self.api_get_call(url, params)
        try:
            if response:
                if response.json().get('responseCode') == 'RESOURCE_NOT_FOUND':
                    return []
                return response.json()
        except (KeyError, AttributeError, NTTMCPAPIException):
            return {}


    def create_vip_node(self, network_domain_id=None, name=None, description=None, ip_address=None, status=None,
                        health_monitor=None, connection_limit=None, connection_rate_limit=None):
        """
        Create a Virtual IP node

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The node name
        :kw description: the node descrition
        :kw ip_address: The IPv4 or IPv6 address of the Node
        :kw status: The status for the node. Valid values are stored in VIP_NODE_STATES in ansible.module_utils.ntt_mcp_config
        :kw health_monitor: The UUID for a node compatible health monitoring profile
        :kw connection_limit: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
        :kw connection_rate_limit: The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
        :returns: The UUID of the newly created node
        """
        params = {}
        if not all([network_domain_id, name, ip_address, status, connection_limit, connection_rate_limit]):
            raise NTTMCPAPIException('Valid values for Network Domain ID, Name, IP Address, status, connection limit '
                                     'and connection rate limit values are required')

        version = get_ip_version(ip_address)
        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['ipv{0}Address'.format(version)] = ip_address
        params['status'] = status
        params['healthMonitorId'] = health_monitor
        params['connectionLimit'] = connection_limit
        params['connectionRateLimit'] = connection_rate_limit

        url = self.base_url + 'networkDomainVip/createNode'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create VIP Node request was accepted')


    def update_vip_node(self, node_id=None, description=None, status=None, health_monitor=None, no_health_monitor=False,
                        connection_limit=None, connection_rate_limit=None):
        """
        :kw node_id: The UUID of the node to be updated
        :kw description: the node description
        :kw status: The status for the node. Valid values are stored in VIP_NODE_STATES in ansible.module_utils.ntt_mcp_config
        :kw health_monitor: The UUID for a node compatible health monitoring profile
        :kw no_health_monitor: If True this will remove any configured health monitoring profiles on the node
        :kw connection_limit: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
        :kw connection_rate_limit: The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
        :returns: The UUID of the newly created node
        """
        params = {}
        if not node_id:
            raise NTTMCPAPIException('Valid values for Network Domain ID and node ID are required ')

        params['id'] = node_id
        if description:
            params['description'] = description
        if status:
            params['status'] = status
        if no_health_monitor:
            params['healthMonitorId'] = {'nil': True}
        elif health_monitor:
            params['healthMonitorId'] = health_monitor
        if connection_limit:
            params['connectionLimit'] = connection_limit
        if connection_rate_limit:
            params['connectionRateLimit'] = connection_rate_limit

        url = self.base_url + 'networkDomainVip/editNode'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update VIP Node request was accepted')


    def remove_vip_node(self, node_id):
        """
        Remove a Virtual IP node

        :arg node_id: UUID of the VIP Node
        :returns: string (API message)
        """
        if node_id is None:
            raise NTTMCPAPIException('A valid value for the VIP Node ID is required')
        params = {'id': node_id}

        url = self.base_url + 'networkDomainVip/deleteNode'

        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove VIP Node request was accepted')


    def list_vip_health_monitor(self, network_domain_id=None):
        """
        Return an array of Virtual IP health monitor profiles

        :kw network_domain_id: The UUID of the Cloud Network Domain
        :returns: List of VIP Node Health Monitor profiles
        """
        params = {}
        if not network_domain_id:
            raise NTTMCPAPIException('The Network Domain ID provided is invalid')
        params['networkDomainId'] = network_domain_id

        url = self.base_url + 'networkDomainVip/defaultHealthMonitor'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('defaultHealthMonitor')
        except Exception:
            return []


    def list_vip_pool(self, network_domain_id=None, name=None):
        """
        Return an array of Virtual IP pools

        :arg network_domain_id: The UUID of a Cloud Network Domain
        :arg name: The pool name
        :returns: List of Nodes
        """
        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain is required')

        params['networkDomainId'] = network_domain_id

        if name:
            params['name'] = name

        url = self.base_url + 'networkDomainVip/pool'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('pool')
        except Exception:
            return []


    def get_vip_pool(self, pool_id):
        """
        Return a specific Virtual IP pool based on the specified UUID

        :arg pool_id: The UUID of a VIP pool
        :returns: List of Pools
        """
        params = {}
        if pool_id is None:
            raise NTTMCPAPIException('The VIP Pool ID is required')

        url = self.base_url + 'networkDomainVip/pool/{0}'.format(pool_id)

        response = self.api_get_call(url, params)
        try:
            return response.json()
        except Exception:
            return {}


    def create_vip_pool(self, network_domain_id=None, name=None, description=None, load_balancing=None,
                        service_down_action=None, health_monitor=None, slow_ramp_time=None):
        """
        Create a new Virtual IP pool

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The node name
        :kw description: The pool description
        :kw ip_address: The IPv4 or IPv6 address of the Node
        :kw load_balancing: The load balancing method for the node. Valid values are stored in LOAD_BALANCING_METHODS in ansible.module_utils.ntt_mcp_config
        :kw health_monitor: List of UUID for a pool compatible health monitoring profiles (maximum of 2 IDs in the list)
        :kw service_down_action: When a Pool Member fails to respond to a Health Monitor, the system marks that Pool Member down and removes any persistence entries associated with the Pool Member.
        :kw slow_ramp_time: The Slow Ramp Time setting controls the percentage of connections that are sent to a new Pool Member by specifying the duration (in seconds)
        :returns: The UUID of the newly created pool
        """
        params = {}
        if not all([network_domain_id, name, load_balancing, service_down_action, slow_ramp_time]):
            raise NTTMCPAPIException('Valid values for Network Domain ID, Name, load balancing method and '
                                     'slow ramp time values are required')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['loadBalanceMethod'] = load_balancing
        params['serviceDownAction'] = service_down_action
        params['healthMonitorId'] = health_monitor
        params['slowRampTime'] = slow_ramp_time

        url = self.base_url + 'networkDomainVip/createPool'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create VIP Pool request was accepted')


    def update_vip_pool(self, vip_pool_id, description=None, load_balancing=None, health_monitor=None,
                        no_health_monitor=None, service_down_action=None, slow_ramp_time=None):
        """
        Update an existing IP Pool
        :kw vip_pool_id: The UUID of the VIP Pool
        :kw description: The description of the VIP Pool
        :kw load_balancing: The load balancing method for the node. Valid values are stored in LOAD_BALANCING_METHODS in ansible.module_utils.ntt_mcp_config
        :kw health_monitor: List of UUID for a pool compatible health monitoring profiles (maximum of 2 IDs in the list)
        :kw no_health_monitor: If this is True all health monitoring profiles will be removed from the VIP Pool
        :kw service_down_action: When a Pool Member fails to respond to a Health Monitor, the system marks that Pool Member down and removes any persistence entries associated with the Pool Member.
        :kw slow_ramp_time: The Slow Ramp Time setting controls the percentage of connections that are sent to a new Pool Member by specifying the duration (in seconds)
        # Return: The UUID of the updated pool
        """
        params = {}
        if not vip_pool_id:
            raise NTTMCPAPIException('A valid VIP Pool ID is required')

        params['id'] = vip_pool_id
        if description:
            params['description'] = description
        if load_balancing:
            params['loadBalanceMethod'] = load_balancing
        if service_down_action:
            params['serviceDownAction'] = service_down_action
        if slow_ramp_time:
            params['slowRampTime'] = slow_ramp_time
        if no_health_monitor:
            params['healthMonitorId'] = {'nil': True}
        elif health_monitor:
            params['healthMonitorId'] = health_monitor

        url = self.base_url + 'networkDomainVip/editPool'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update VIP Pool request was accepted')


    def remove_vip_pool(self, vip_pool_id=None):
        """
        Remove a VIP Pool
        :kw vip_pool_id: The UUID of the VIP Pool
        """
        params = {}
        if not vip_pool_id:
            raise NTTMCPAPIException('A valid VIP Pool ID is required')

        params['id'] = vip_pool_id

        url = self.base_url + 'networkDomainVip/deletePool'

        response = self.api_post_call(url, params)
        try:
            if response.json()['responseCode'] == "OK":
                return response.json()['message']
            else:
                return response.json()['error']
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove VIP Pool request was accepted')


    def list_vip_pool_members(self, vip_pool_id=None):
        """
        List all the members for the given VIP Pool ID
        :kw vip_pool_id: The UUID of the VIP Pool
        :returns: A list of members
        """
        params = {}
        if not vip_pool_id:
            raise NTTMCPAPIException('A valid VIP Pool ID is required')

        params['poolId'] = vip_pool_id

        url = self.base_url + 'networkDomainVip/poolMember'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('poolMember')
        except (KeyError, IndexError):
            return []


    def add_vip_pool_member(self, vip_pool_id=None, vip_node_id=None, port=None, status=None):
        """
        Add a member to an existing VIP Pool

        :kw vip_pool_id: The UUID of the VIP Pool
        :kw vip_node_id: The UUID of the Node to be added
        :kw port: The TCP/UDP port to be used
        :kw status: The status for the node. Valid values are stored in VIP_NODE_STATES in ansible.module_utils.ntt_mcp_config
        :returns: The UUID of the new VIP Pool Member
        """
        params = {}
        if not all([vip_pool_id, vip_node_id, port, status]):
            raise NTTMCPAPIException('Valid values for VIP Pool ID, VIP Node ID, port and status are required')

        params['poolId'] = vip_pool_id
        params['nodeId'] = vip_node_id
        params['port'] = port
        params['status'] = status

        url = self.base_url + 'networkDomainVip/addPoolMember'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the add VIP Pool Member request was accepted')


    def remove_vip_pool_member(self, vip_pool_member_id):
        """
        Remove a member to an existing VIP Pool

        :kw vip_pool_member_id: The UUID of the Node to be removed
        :returns: string API message
        """
        if vip_pool_member_id is None:
            raise NTTMCPAPIException('A valid value for the VIP Node ID is required')
        params = {'id': vip_pool_member_id}

        url = self.base_url + 'networkDomainVip/removePoolMember'

        response = self.api_post_call(url, params)
        try:
            if response.json().get('responseCode') == "OK":
                return response.json().get('message')
            else:
                return response.json().get('error')
        except (KeyError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the remove VIP Pool Member request was accepted')


    def list_vip_ssl(self, network_domain_id=None, ssl_type=None, name=None):
        """
        List the VIP SSL object

        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw ssl_type: The type of SSL object to list
        :kw name: The name of the SSL object
        """
        params = {}

        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain and the SSL object type cannot be None')
        elif ssl_type not in ['sslDomainCertificate', 'sslCertificateChain', 'sslOffloadProfile']:
            raise NTTMCPAPIException('Invalid object type')

        if name:
            params['name'] = name

        url = self.base_url + 'networkDomainVip/{0}'.format(ssl_type)

        response = self.api_get_call(url, params)
        try:
            return response.json().get(ssl_type)
        except (KeyError, IndexError, AttributeError):
            return []


    def get_vip_ssl(self, ssl_type=None, ssl_id=None):
        """
        Get a VIP SSL object

        :kw ssl_type: The type of SSL object to get
        :kw ssl_id: The UUID of the SSL object
        """
        if ssl_id is None:
            raise NTTMCPAPIException('SSL object ID cannot be None')
        elif ssl_type not in ['sslDomainCertificate', 'sslCertificateChain', 'sslOffloadProfile']:
            raise NTTMCPAPIException('Invalid object type')

        if ssl_type == 'certificate':
            ssl_type = 'sslDomainCertificate'
        elif ssl_type == 'chain':
            ssl_type = 'sslCertificateChain'
        elif ssl_type == 'profile':
            ssl_type = 'sslOffloadProfile'

        url = self.base_url + 'networkDomainVip/{0}/{1}'.format(ssl_type, ssl_id)

        response = self.api_get_call(url, None)
        try:
            if response.json().get('responseCode') == 'RESOURCE_NOT_FOUND':
                return []
            return response.json()
        except (KeyError, IndexError, AttributeError):
            return {}


    def import_ssl_cert(self, network_domain_id=None, name=None, description=None, cert=None, cert_key=None):
        """
        Import a SSL certificate

        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw name: The name of the SSL certificate
        :kw description: The description of the SSL certificate
        :kw cert: The SSL certificate
        :kw cert_key: The SSL certificate key
        """
        params = {}
        if not all([network_domain_id, name, cert, cert_key]):
            raise NTTMCPAPIException('A valid Network Domain, certificate name, certificate and key are required')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['certificate'] = cert
        params['key'] = cert_key

        url = self.base_url + 'networkDomainVip/importSslDomainCertificate'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the import SSL certificate request was accepted')


    def import_ssl_cert_chain(self, network_domain_id=None, name=None, description=None, cert_chain=None):
        """
        Import a SSL certificate chain

        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw name: The name of the SSL certificate chain
        :kw description: The description of the SSL certificate chain
        :kw cert_chain: The SSL certificate chain
        """
        params = {}
        if not all([network_domain_id, name, cert_chain]):
            raise NTTMCPAPIException('A valid Network Domain, certificate chain name, certificate chain are required')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['certificateChain'] = cert_chain

        url = self.base_url + 'networkDomainVip/importSslCertificateChain'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the import SSL certificate chain request was accepted')


    def create_ssl_offload_profile(self, network_domain_id=None, name=None, description=None, ciphers=None, cert_id=None, cert_chain_id=None):
        """
        Import a SSL certificate chain

        :kw network_domain_id: The UUID of the Cloud Network Domain
        :kw name: The name of the SSL certificate chain
        :kw description: The description of the SSL certificate chain
        :kw ciphers: A valid F5 cipher string
        :kw cert_id: The UUID of a previously imported SSL certificate
        :kw cerT_chain_id: the UUID of the previously imported SSL certificate chain
        """
        params = {}
        if not all([network_domain_id, name, ciphers, cert_id, cert_chain_id]):
            raise NTTMCPAPIException('A valid Network Domain, profile name, cipher string, certificate ID and certificate chain ID are required')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['ciphers'] = ciphers
        params['sslDomainCertificateId'] = cert_id
        params['sslCertificateChainId'] = cert_chain_id

        url = self.base_url + 'networkDomainVip/createSslOffloadProfile'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the create SSL Offload Profile request was accepted')


    def update_ssl_offload_profile(self, profile_id=None, name=None, description=None, ciphers=None, cert_id=None, cert_chain_id=None):
        """
        Import a SSL certificate chain

        :kw profile_id: The UUID of the SSL Offload Profile
        :kw name: The name of the SSL certificate chain
        :kw description: The description of the SSL certificate chain
        :kw ciphers: A valid F5 cipher string
        :kw cert_id: The UUID of a previously imported SSL certificate
        :kw cerT_chain_id: the UUID of the previously imported SSL certificate chain
        """
        params = {}
        if not all([profile_id, name]):
            raise NTTMCPAPIException('A valid profile ID and profile name are required')

        params['id'] = profile_id
        params['name'] = name
        if description:
            params['description'] = description
        if ciphers:
            params['ciphers'] = ciphers
        if cert_id:
            params['sslDomainCertificateId'] = cert_id
        if cert_chain_id:
            params['sslCertificateChainId'] = cert_chain_id

        url = self.base_url + 'networkDomainVip/editSslOffloadProfile'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('responseCode')
        except (KeyError, IndexError, AttributeError):
            raise NTTMCPAPIException('Could not confirm that the update SSL Offload Profile request was accepted')



    def remove_ssl(self, ssl_type=None, ssl_id=None):
        """
        Remove a VIP SSL object

        :kw ssl_type: The type of SSL object to remove
        :kw ssl_id: The UUID of the SSL object
        """
        if ssl_id is None:
            raise NTTMCPAPIException('SSL object ID cannot be None')
        elif ssl_type not in ['certificate', 'chain', 'profile']:
            raise NTTMCPAPIException('Invalid object type')

        if ssl_type == 'certificate':
            ssl_type = 'deleteSslDomainCertificate'
        elif ssl_type == 'chain':
            ssl_type = 'deleteSslCertificateChain'
        elif ssl_type == 'profile':
            ssl_type = 'deleteSslOffloadProfile'

        params = {}
        params['id'] = ssl_id

        url = self.base_url + 'networkDomainVip/{0}'.format(ssl_type)

        response = self.api_post_call(url, params)
        try:
            return response.json()
        except Exception as e:
            raise NTTMCPAPIException('{0}'.format(e))


    def list_vip_listener(self, network_domain_id=None, name=None):
        """
        List VIP Virtual Listeners

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The name to search for
        :returns: A list of Virtual Listeners
        """
        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain is required')

        if name:
            params['name'] = name

        url = self.base_url + 'networkDomainVip/virtualListener'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('virtualListener')
        except Exception:
            return []


    def get_vip_listener(self, listener_id):
        """
        List VIP Virtual Listeners

        :kw listener_id: The UUID of a Virtual Listener
        :returns: A Virtual Listeners
        """
        params = {}
        if listener_id is None:
            raise NTTMCPAPIException('The VIP Virtual Listener ID is required')

        url = self.base_url + 'networkDomainVip/virtualListener/{0}'.format(listener_id)

        response = self.api_get_call(url, params)
        try:
            if response.json().get('responseCode') == 'RESOURCE_NOT_FOUND':
                return {}
            return response.json()
        except Exception:
            return {}



    def list_irule(self, network_domain_id=None, name=None):
        """
        List VIP iRules

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The name to search for
        :returns: A list of iRules
        """

        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain is required')

        params['networkDomainId'] = network_domain_id
        if name:
            params['name'] = name

        url = self.base_url + 'networkDomainVip/defaultIrule'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('defaultIrule')
        except Exception:
            return []


    def list_persistence_profile(self, network_domain_id=None, name=None):
        """
        List VIP Persistence Profiles

        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The name to search for
        :returns: A list of Persistence Profiles
        """

        params = {}
        if network_domain_id is None:
            raise NTTMCPAPIException('Network Domain is required')

        params['networkDomainId'] = network_domain_id
        if name:
            params['name'] = name

        url = self.base_url + 'networkDomainVip/defaultPersistenceProfile'

        response = self.api_get_call(url, params)
        try:
            return response.json().get('defaultPersistenceProfile')
        except Exception:
            return []


    def create_vip_listener(self, network_domain_id=None, name=None, description=None, listener_type='STANDARD',
                            protocol='ANY', ip_address=None, port=None, enabled=True, connection_limit=100000,
                            connection_rate_limit=4000, preservation=None, pool_id_1=None, pool_id_2=None,
                            persistence_id_1=None, persistence_id_2=None, optimization_profile=None,
                            ssl_profile_id=None, irules=None):
        """
        Create a VIP Virtual Listener

        :arg self: this
        :kw network_domain_id: The UUID of a Cloud Network Domain
        :kw name: The name of the Virtual Listener
        :kw description: The description for the Virtual Listener (max 255 characters)
        :kw type: The type of Virtual Listener
        :kw protocol: The protocol for this Virtual Listener
        :kw ip_address: The IP address to listen on
        :kw port: The port(s) to listen on
        :kw enabled: The state for this Virtual Listener
        :kw connection_limit: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
        :kw connection_rate_limit: The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
        :kw preservation: Identifies how the port of the source traffic will be treated when sending connections to the pool member.
        :kw pool_id_1: The primary VIP Pool
        :kw pool_id_2: The client VIP Pool (gets a duplicate copy of all VIP traffic)
        :kw persistence_id_1: The UUID of the primary persistence profile
        :kw persistence_id_2: The UUID of the secondary persistence profile
        :kw optimization_profile: The optimization profile
        :kw ssl_profile_id: The UUID of the SSL Offload Profile
        :kw irules: A list of UUIDs of iRules
        """
        params = {}

        if not all([network_domain_id, name, ip_address, pool_id_1]):
            raise NTTMCPAPIException('A valid Network Domain ID, name, IP Address and VIP Pool are required.')

        params['networkDomainId'] = network_domain_id
        params['name'] = name
        if description:
            params['description'] = description
        params['type'] = listener_type
        params['protocol'] = protocol
        params['listenerIpAddress'] = ip_address
        if port:
            params['port'] = port
        params['enabled'] = enabled
        params['connectionLimit'] = connection_limit
        params['connectionRateLimit'] = connection_rate_limit
        params['sourcePortPreservation'] = preservation
        params['poolId'] = pool_id_1
        if pool_id_2:
            params['clientClonePoolId'] = pool_id_2
        if persistence_id_1:
            params['persistenceProfileId'] = persistence_id_1
        if persistence_id_2:
            params['fallbackPersistenceProfileId'] = persistence_id_2
        if optimization_profile:
            params['optimizationProfile'] = optimization_profile
        if ssl_profile_id:
            params['sslOffloadProfileId'] = ssl_profile_id
        if type(irules) is list:
            if irules:
                params['iruleId'] = irules

        url = self.base_url + 'networkDomainVip/createVirtualListener'

        response = self.api_post_call(url, params)
        try:
            return response.json().get('info')[0].get('value')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the create VIP Virtual Listener request was accepted')


    def update_vip_listener(self, listener_id=None, description=None, listener_type='STANDARD',
                            protocol='ANY', enabled=True, connection_limit=100000,
                            connection_rate_limit=4000, preservation=None, pool_id_1=None, pool_id_2=None,
                            persistence_id_1=None, persistence_id_2=None, optimization_profile=None,
                            ssl_profile_id=None, irules=None):
        """
        Create a VIP Virtual Listener

        :arg self: this
        :kw listener_id: The UUID of the Virtual Listener
        :kw description: The description for the Virtual Listener (max 255 characters)
        :kw type: The type of Virtual Listener
        :kw protocol: The protocol for this Virtual Listener
        :kw enabled: The state for this Virtual Listener
        :kw connection_limit: The maximum number of simultaneous connections permitted on the Node. Should be an integer between 1 and 100,000
        :kw connection_rate_limit: The amount of new connections permitted every second. Should be an integer between 1 and 4,000.
        :kw preservation: Identifies how the port of the source traffic will be treated when sending connections to the pool member.
        :kw pool_id_1: The primary VIP Pool
        :kw pool_id_2: The client VIP Pool (gets a duplicate copy of all VIP traffic)
        :kw persistence_id_1: The UUID of the primary persistence profile
        :kw persistence_id_2: The UUID of the secondary persistence profile
        :kw optimization_profile: The optimization profile
        :kw ssl_profile_id: The UUID of the SSL Offload Profile
        :kw irules: A list of UUIDs of iRules
        """
        params = {}

        if not listener_id:
            raise NTTMCPAPIException('A valid VIP Listener ID is required.')

        params['id'] = listener_id
        params['description'] = description
        params['type'] = listener_type
        params['protocol'] = protocol
        params['enabled'] = enabled
        params['connectionLimit'] = connection_limit
        params['connectionRateLimit'] = connection_rate_limit
        params['sourcePortPreservation'] = preservation
        params['poolId'] = pool_id_1
        params['clientClonePoolId'] = pool_id_2
        params['persistenceProfileId'] = persistence_id_1
        params['fallbackPersistenceProfileId'] = persistence_id_2
        params['optimizationProfile'] = optimization_profile
        params['sslOffloadProfileId'] = ssl_profile_id
        if type(irules) is list:
            params['iruleId'] = irules

        url = self.base_url + 'networkDomainVip/editVirtualListener'

        response = self.api_post_call(url, params)
        try:
            if response.json().get('responseCode') == "OK":
                return listener_id
            else:
                return response.json().get('error')
        except (KeyError, IndexError):
            raise NTTMCPAPIException('Could not confirm that the update VIP Virtual Listener request was accepted')


    def remove_vip_listener(self, listener_id=None):
        """
        Remove a VIP Pool
        :kw listener_id: The UUID of the VIP Virtual Listener
        """
        params = {}
        if not listener_id:
            raise NTTMCPAPIException('A valid VIP Virtual Listener ID is required')

        params['id'] = listener_id

        url = self.base_url + 'networkDomainVip/deleteVirtualListener'

        response = self.api_post_call(url, params)
        try:
            if response.json().get('responseCode') == "OK":
                return response.json().get('message')
            else:
                return response.json().get('error')
        except KeyError:
            raise NTTMCPAPIException('Could not confirm that the remove VIP Virtual Listener request was accepted')

    #
    # API Calls
    #
    def api_get_call(self, url, params=None):
        """
        Process a GET API call to the Cloud Control API

        :arg url: The url for the API call
        :kw params: The parameters for the GET request
        :returns: API response
        """
        response = REQ.get(url, auth=self.credentials, headers=HTTP_HEADERS, params=params)
        try:
            if response != None:
                if response.status_code == 200:
                    return response
                elif response.json().get('responseCode') == 'RESOURCE_NOT_FOUND':
                    #raise Exception('No object found')
                    return response
                else:
                    raise NTTMCPAPIException(response.text)
            else:
                raise Exception('No response from the API for url: {0}'.format(url))
        except Exception as e:
            raise NTTMCPAPIException('{0} {1}'.format(e, response.text))


    def api_post_call(self, url, params):
        """
        Process a POST API call to the Cloud Control API

        :arg url: The url for the API call
        :kw params: The parameters for the POST request
        :returns: API response
        """
        response = REQ.post(url, auth=self.credentials, headers=HTTP_HEADERS, json=params)
        try:
            if response != None:
                if response.status_code == 200:
                    return response
                else:
                    raise Exception('{0}'.format(response.text))
            else:
                raise Exception('No response from the API for url: {0}'.format(url))
        except Exception as e:
            raise NTTMCPAPIException('{0} {1}'.format(e, response.text))
