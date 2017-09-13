#!/usr/bin/python
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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_router
short_description: Create or delete routers from OpenStack
extends_documentation_fragment: openstack
version_added: "2.0"
author: "David Shrewsbury (@Shrews)"
description:
   - Create or Delete routers from OpenStack. Although Neutron allows
     routers to share the same name, this module enforces name uniqueness
     to be more user friendly.
options:
   state:
     description:
        - Indicate desired state of the resource
     choices: ['present', 'absent']
     default: present
   name:
     description:
        - Name to be give to the router
     required: true
   admin_state_up:
     description:
        - Desired admin state of the created or existing router.
     required: false
     default: true
   enable_snat:
     description:
        - Enable Source NAT (SNAT) attribute.
     required: false
     default: true
   network:
     description:
        - Unique name or ID of the external gateway network.
        - required I(interfaces) or I(enable_snat) are provided.
     required: false
     default: None
   project:
     description:
        - Unique name or ID of the project.
     required: false
     default: None
     version_added: "2.2"
   external_fixed_ips:
     description:
        - The IP address parameters for the external gateway network. Each
          is a dictionary with the subnet name or ID (subnet) and the IP
          address to assign on the subnet (ip). If no IP is specified,
          one is automatically assigned from that subnet.
     required: false
     default: None
   interfaces:
     description:
        - List of subnets to attach to the router internal interface.
     required: false
     default: None
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements: ["shade"]
'''

EXAMPLES = '''
# Create a simple router, not attached to a gateway or subnets.
- os_router:
    cloud: mycloud
    state: present
    name: simple_router

# Create a simple router, not attached to a gateway or subnets for a given project.
- os_router:
    cloud: mycloud
    state: present
    name: simple_router
    project: myproj

# Creates a router attached to ext_network1 on an IPv4 subnet and one
# internal subnet interface.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    external_fixed_ips:
      - subnet: public-subnet
        ip: 172.24.4.2
    interfaces:
      - private-subnet

# Update existing router1 external gateway to include the IPv6 subnet.
# Note that since 'interfaces' is not provided, any existing internal
# interfaces on an existing router will be left intact.
- os_router:
    cloud: mycloud
    state: present
    name: router1
    network: ext_network1
    external_fixed_ips:
      - subnet: public-subnet
        ip: 172.24.4.2
      - subnet: ipv6-public-subnet
        ip: 2001:db8::3

# Delete router1
- os_router:
    cloud: mycloud
    state: absent
    name: router1
'''

RETURN = '''
router:
    description: Dictionary describing the router.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        id:
            description: Router ID.
            type: string
            sample: "474acfe5-be34-494c-b339-50f06aa143e4"
        name:
            description: Router name.
            type: string
            sample: "router1"
        admin_state_up:
            description: Administrative state of the router.
            type: boolean
            sample: true
        status:
            description: The router status.
            type: string
            sample: "ACTIVE"
        tenant_id:
            description: The tenant ID.
            type: string
            sample: "861174b82b43463c9edc5202aadc60ef"
        external_gateway_info:
            description: The external gateway parameters.
            type: dictionary
            sample: {
                      "enable_snat": true,
                      "external_fixed_ips": [
                         {
                           "ip_address": "10.6.6.99",
                           "subnet_id": "4272cb52-a456-4c20-8f3c-c26024ecfa81"
                         }
                       ]
                    }
        routes:
            description: The extra routes configuration for L3 router.
            type: list
'''
try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion

ROUTER_INTERFACE_OWNERS = set([
    'network:router_interface',
    'network:router_interface_distributed',
    'network:ha_router_replicated_interface'
])


def _router_internal_interfaces(cloud, router):
    for port in cloud.list_router_interfaces(router, 'internal'):
        if port['device_owner'] in ROUTER_INTERFACE_OWNERS:
            yield port


def _needs_update(cloud, module, router, network, internal_subnet_ids, internal_port_ips, internal_port_ids):
    """Decide if the given router needs an update.
    """
    if router['admin_state_up'] != module.params['admin_state_up']:
        return True
    if router['external_gateway_info']:
        if router['external_gateway_info'].get('enable_snat', True) != module.params['enable_snat']:
            return True
    if network:
        if not router['external_gateway_info']:
            return True
        elif router['external_gateway_info']['network_id'] != network['id']:
            return True

    # check external interfaces
    if module.params['external_fixed_ips']:
        for new_iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(new_iface['subnet'])
            exists = False

            # compare the requested interface with existing, looking for an existing match
            for existing_iface in router['external_gateway_info']['external_fixed_ips']:
                if existing_iface['subnet_id'] == subnet['id']:
                    if 'ip' in new_iface:
                        if existing_iface['ip_address'] == new_iface['ip']:
                            # both subnet id and ip address match
                            exists = True
                            break
                    else:
                        # only the subnet was given, so ip doesn't matter
                        exists = True
                        break

            # this interface isn't present on the existing router
            if not exists:
                return True

    # check internal interfaces
    if module.params['interfaces']:
        existing_subnet_ids = []
        existing_internal_port_ips = []
        existing_internal_port_ids = []
        for port in _router_internal_interfaces(cloud, router):
            existing_internal_port_ids.append(port.id)
            if 'fixed_ips' in port:
                for fixed_ip in port['fixed_ips']:
                    existing_subnet_ids.append(fixed_ip['subnet_id'])
                    existing_internal_port_ips.append(fixed_ip['ip_address'])

        x=set(existing_internal_port_ids)
        z=set(internal_port_ids)
        #module.fail_json(msg='bhujay hyyere subnet ... supplied =  % s  and existing = % s ' % (internal_subnet_ids, existing_subnet_ids))
        #module.fail_json(msg='bhujay hyyere ... supplied =  % s  and existing = % s ' % (z, x))
        if set(internal_subnet_ids) != set(existing_subnet_ids):
              #module.fail_json(msg='bhujay hyyere subnet ... supplied =  % s  and existing = % s ' % (internal_subnet_ids, existing_subnet_ids))
              return True
        #if set(internal_port_ips) != set(existing_internal_port_ips):
        if set(internal_port_ids) != set(existing_internal_port_ids):
               #module.fail_json(msg='bhujay hyyere . port ids.. supplied =  % s  and existing = % s ' % (z, x))
               return True


    return False


def _system_state_change(cloud, module, router, network, internal_ids, internal_portips, internal_portids):
    """Check if the system state would be changed."""

    #module.fail_json(msg='system state chage ...bhujay here % s' % internal_portids)
    state = module.params['state']
    if state == 'absent' and router:
        return True
    if state == 'present':
        if not router:
            return True
        return _needs_update(cloud, module, router, network, internal_ids, internal_portips, internal_portids)
    return False


def _build_kwargs(cloud, module, router, network):
    kwargs = {
        'admin_state_up': module.params['admin_state_up'],
    }

    if router:
        kwargs['name_or_id'] = router['id']
    else:
        kwargs['name'] = module.params['name']

    if network:
        kwargs['ext_gateway_net_id'] = network['id']
        # can't send enable_snat unless we have a network
        kwargs['enable_snat'] = module.params['enable_snat']

    if module.params['external_fixed_ips']:
        kwargs['ext_fixed_ips'] = []
        for iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(iface['subnet'])
            d = {'subnet_id': subnet['id']}
            if 'ip' in iface:
                d['ip_address'] = iface['ip']
            kwargs['ext_fixed_ips'].append(d)

    return kwargs


def _validate_subnets(module, cloud):
    external_subnet_ids = []
    internal_subnet_ids = []
    internal_port_ips = []
    internal_port_ids = []
    existing_port_ips = []
    existing_port_ids = []
    existings_ports = []
    existing_port_attrib = {}
    if module.params['external_fixed_ips']:
        for iface in module.params['external_fixed_ips']:
            subnet = cloud.get_subnet(iface['subnet'])
            if not subnet:
                module.fail_json(msg='subnet %s not found' % iface['subnet'])
            external_subnet_ids.append(subnet['id'])

    if module.params['interfaces']:
        for iface in module.params['interfaces']:
            subnet = cloud.get_subnet(iface['subnet'])
            net = cloud.get_network(iface['net'])
            if not net:
                module.fail_json(msg='net %s not found' % iface['net'])
            if not subnet:
                module.fail_json(msg='subnet %s not found' % iface['subnet'])
            if not ("portip" in  iface):
                internal_subnet_ids.append(subnet['id'])
            elif not iface['portip']:
                module.fail_json(msg='put an ip in portip or  remove it from list to assign default port to router') 
            else:
                 for existing_port in cloud.list_ports(filters={'network_id':net.id}):
                    #existing_port_attrib['p_id'] = existing_port.id
                    for fixed_ip in existing_port['fixed_ips']:
                        if iface['portip'] == fixed_ip['ip_address']:
                          internal_port_ids.append(existing_port.id)
                          existing_port_ips.append(fixed_ip['ip_address'])
                        #existing_port_attrib['p_ip'] = existing_port.id

                 if iface['portip'] in   existing_port_ips:
                    internal_port_ips.append(iface['portip'])
                 else:
                    p = cloud.create_port(network_id=net.id,fixed_ips=[{'ip_address':iface['portip'],'subnet_id':subnet.id}])
                    if p:
                        internal_port_ips.append(iface['portip'])
                        internal_port_ids.append(p.id)
                    #module.fail_json(msg='port with ip  %s not found' % iface['portip'])
 
                           # module.fail_json(msg='port with ip  %s not found' %  fixed_ip['ip_address'])
                           # module.fail_json(msg= existing_port_ips)

    #module.fail_json(msg= existing_port_ips)
    #module.fail_json(msg=internal_port_ips)
    #module.fail_json(msg=internal_port_ids)
   # module.fail_json(msg=internal_subnet_ids)
                           
    return external_subnet_ids, internal_subnet_ids , internal_port_ips, internal_port_ids


def main():
    argument_spec = openstack_full_argument_spec(
        state=dict(default='present', choices=['absent', 'present']),
        name=dict(required=True),
        admin_state_up=dict(type='bool', default=True),
        enable_snat=dict(type='bool', default=True),
        network=dict(default=None),
        interfaces=dict(type='list', default=None),
        external_fixed_ips=dict(type='list', default=None),
        project=dict(default=None)
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(argument_spec,
                           supports_check_mode=True,
                           **module_kwargs)
   # module.fail_json(msg='Bhujay ....here')

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    if (module.params['project'] and
            StrictVersion(shade.__version__) <= StrictVersion('1.9.0')):
        module.fail_json(msg="To utilize project, the installed version of"
                             "the shade library MUST be > 1.9.0")

    state = module.params['state']
    name = module.params['name']
    network = module.params['network']
    project = module.params['project']

    if module.params['external_fixed_ips'] and not network:
        module.fail_json(msg='network is required when supplying external_fixed_ips')

    try:
        cloud = shade.openstack_cloud(**module.params)
        if project is not None:
            proj = cloud.get_project(project)
            if proj is None:
                module.fail_json(msg='Project %s could not be found' % project)
            project_id = proj['id']
            filters = {'tenant_id': project_id}
        else:
            project_id = None
            filters = None

        router = cloud.get_router(name, filters=filters)
        net = None
        if network:
            net = cloud.get_network(network)
            if not net:
                module.fail_json(msg='network %s not found' % network)

        # Validate and cache the subnet IDs so we can avoid duplicate checks
        # and expensive API calls.
        external_ids, internal_ids, internal_portips, internal_portids = _validate_subnets(module, cloud)
        #module.fail_json(msg='bhujay hyyere ... % s' % internal_portids)
        if module.check_mode:
            module.exit_json(
                changed=_system_state_change(cloud, module, router, net, internal_ids, internal_portips, internal_portids)
            )

        if state == 'present':
            changed = False

            if not router:
                kwargs = _build_kwargs(cloud, module, router, net)
                if project_id:
                    kwargs['project_id'] = project_id
                router = cloud.create_router(**kwargs)
                for internal_subnet_id in internal_ids:
                    cloud.add_router_interface(router, subnet_id=internal_subnet_id)
                changed = True
                # add interface by port id as well
                #for internal_port_id in internal_portids:
                #    cloud.add_router_interface(router, port_id=internal_port_id)
                #changed = True
            else:
                if _needs_update(cloud, module, router, net, internal_ids, internal_portips, internal_portids):
                    #module.fail_json(msg='bhujay reached  to update router section with subnet ids %s and ports= %s ' %(internal_ids,internal_portids))
                    kwargs = _build_kwargs(cloud, module, router, net)
                    updated_router = cloud.update_router(**kwargs)
                   # module.fail_json(msg='bhujay reached  updated router = %s ' % updated_router)

                    # Protect against update_router() not actually
                    # updating the router.
                    if not updated_router:
                        changed = False

                    # On a router update, if any internal interfaces were supplied,
                    # just detach all existing internal interfaces and attach the new.
                   # elif (not  internal_ids) or (not internal_portids):
                   #     module.fail_json(msg='bhujay when no subnet id ir portid was returned by validate function')
                   #     router = updated_router
                   #     ports = _router_internal_interfaces(cloud, router)
                   #     for port in ports:
                   #         cloud.remove_router_interface(router, port_id=port['id'])
                   #     changed = True


                    elif internal_ids:
                        module.fail_json(msg='bhujay when  subnet id  was returned by validate function')
                        router = updated_router
                        ports = _router_internal_interfaces(cloud, router)
                        for port in ports:
                            cloud.remove_router_interface(router, port_id=port['id'])
                        for internal_subnet_id in internal_ids:
                            cloud.add_router_interface(router, subnet_id=internal_subnet_id)
                        changed = True

                    elif internal_portids:
                        #module.fail_json(msg='bhujay when  port id   was returned by validate function ports= %s' % internal_portids)
                        router = updated_router
                        ports = _router_internal_interfaces(cloud, router)
                        for port in ports:
                            cloud.remove_router_interface(router, port_id=port['id'])
                        for internal_port_id in internal_portids:
                            cloud.add_router_interface(router, port_id=internal_port_id)
                        changed = True

            module.exit_json(changed=changed,
                             router=router,
                             id=router['id'])

        elif state == 'absent':
            if not router:
                module.exit_json(changed=False)
            else:
                # We need to detach all internal interfaces on a router before
                # we will be allowed to delete it.
                ports = _router_internal_interfaces(cloud, router)
                router_id = router['id']
                for port in ports:
                    cloud.remove_router_interface(router, port_id=port['id'])
                cloud.delete_router(router_id)
                module.exit_json(changed=True)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e))
        #module.fail_json(msg='are we here bhujay ..')


# this is magic, see lib/ansible/module_common.py
from ansible.module_utils.basic import *
from ansible.module_utils.openstack import *
if __name__ == '__main__':
    main()
