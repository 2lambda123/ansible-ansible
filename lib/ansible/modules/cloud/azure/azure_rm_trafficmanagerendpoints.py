#!/usr/bin/python
#
# Copyright (c) 2016 Julio Colon, <julio.colon@microsoft.com>
#                    Diego Casati, <diego.casati@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'curated'}


DOCUMENTATION = '''
---
module: azure_rm_trafficmanagerendpoints
version_added: "2.4"
short_description: Manage Azure Traffic Manager (endpoints).
description:
    - Create, update and delete a traffic manager endpoints.
options:
    name:
        description:
             - The name of the Traffic Manager endpoints.
        default: false
        required: true
    resource_group:
        description:
             - The name of the resource group containing the Traffic Manager endpoints.
        required: true
    endpoint_name:
        description:
            - The name of the Traffic Manager endpoint to be created or updated.        
    required: true
    endpoint_type:
        description:
            - The type of the Traffic Manager endpoint to be created or updated.
    # XXX
    target_resource_id:
        description:
            - The Azure Resource URI of the of the endpoint. Not applicable to 
            endpoints of type 'ExternalEndpoints'.
    target:
        description:
            - The fully-qualified DNS name of the endpoint. Traffic Manager 
            returns this value in DNS responses to direct traffic to this endpoint.
    endpoint_status:
        description:
            - The status of the endpoint. If the endpoint is Enabled, it is probed 
            for endpoint health and is included in the traffic routing method. 
        choices:
            - Enabled 
            - Disabled
    weight:
        description:
            - The weight of this endpoint when using the 'Weighted' traffic routing method. 
            Possible values are from 1 to 1000.
    priority:
        description:
            - The priority of this endpoint when using the ‘Priority’ traffic routing method.
             Possible values are from 1 to 1000, lower values represent higher priority. 
             This is an optional parameter. If specified, it must be specified on all endpoints, 
             and no two endpoints can share the same priority value.
    endpoint_location:
        description:
            - Specifies the location of the external or nested endpoints when using the ‘Performance’ 
            traffic routing method.
    min_child_endpoints:
        description:
            - The minimum number of endpoints that must be available in the child profile in order 
            for the parent profile to be considered available. Only applicable to endpoint of type 'NestedEndpoints'.
    geo_mapping:
        description:
            - The list of countries/regions mapped to this endpoint when using the ‘Geographic’ traffic routing method. 
            Please consult Traffic Manager Geographic documentation for a full list of accepted values.
    state:
        description:
            - Assert the state of the resource group. Use 'present' to create or update and
              'absent' to delete. When 'absent' a resource group containing resources 
              will not be removed unless the force option is used.
        default: present
        choices:
            - absent
            - present
        required: false
extends_documentation_fragment:
    - azure
    - azure_tags

author:
    - "Julio Colon (@code4clouds)"
    - "Diego Casati (@diegocasati)"

'''

EXAMPLES = '''
    - name: Create a Traffic Manager endpoint
    azure_rm_trafficmanagerendpoints:
      resource_group: "ContosoRG"
      profile_name: "contoso.com"
      endpoint_name: "Contoso South Central US"
      endpoint_type: "ExternalEndpoints"
      properties:
        target: "ww2.contoso.com"
        endpoint_status: "Enabled"
        endpoint_location: "South Central US"

    - name: Delete a Traffic Manager endpoint
    azure_rm_trafficmanagerendpoints:
      resource_group: "ContosoRG"
      profile_name: "contoso.com"
      state: "absent"
      endpoint_name: "Contoso South Central US"
      endpoint_type: "ExternalEndpoints"
'''
RETURN = '''
contains_resources:
    description: Contains associated resources.
    returned: always
    type: bool
    sample: True
state:
    description: Current state of the resource group.
    returned: always
    type: dict
    sample: {
        "id": "/subscriptions/XXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXX/resourceGroups/Testing",
        "location": "westus",
        "name": "Testing",
        "provisioning_state": "Succeeded",
        "tags": {
            "delete": "on-exit",
            "testing": "no"
        }
    }
'''

try:
    from msrestazure.azure_exceptions import CloudError
    from azure.mgmt.trafficmanager.models import Endpoint, Profile
except ImportError:
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase


def trafficmanagerendpoints_group_to_dict(tm):
    return dict(
        id=tm.id,
        name=tm.name,
        resource_group=tm.resource_group,
        endpoint_type=tm.endpoint_type,
        tags=tm.tags,
    )


class AzureRMTrafficManagerEndpoints(AzureRMModuleBase):

    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(type='str', required=True),
            profile_name=dict(type='str', required=True),
            endpoint_type=dict(type='str'),
            endpoint_name=dict(type='str'),
            properties=dict(type='dict'),
            status=dict(type='str', default='Enabled', choices=['Enabled', 'Disabled']),
            state=dict(type='str', default='present', choices=['present', 'absent'])
        )

        self.resource_group = None
        self.profile_name = None
        self.endpoint_type = None
        self.endpoint_name = None
        self.properties = None
        self.status = None
        self.state = None

        self.results = dict(
            changed=False,
            contains_endpoints=False,
            state=dict(),
        )

        super(AzureRMTrafficManagerEndpoints, self).__init__(self.module_arg_spec,
                                                    supports_check_mode=True)

    def exec_module(self, **kwargs):

        # Collect all the tags and add them to the attributes
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])

        self.results['check_mode'] = self.check_mode

        # Initialize the Ansible return
        results = dict()
        changed = False


        try:
            if self.state == 'present':
                self.log('Fetching traffic manager profile {0}'.format(self.profile_name))

                endpoint = self.create_or_update_traffic_manager_endpoints(self.resource_group, self.profile_name,
                                                                self.endpoint_type, self.endpoint_name, self.properties)


                #results = self.endpoint_to_dict(endpoint, self.resource_group, self.profile_name,
                #                                       self.endpoint_type, self.endpoint_name, self.properties)
                changed = True
                if endpoint is None:
                    results['status'] = 'Created'
                else:
                    results['status'] = 'Updated'

            elif self.state == 'absent':
                self.log('Deleting traffic manager endpoint {0}'.format(self.endpoint_name))
                endpoint = self.trafficmanager_client.endpoints.get(self.resource_group, self.profile_name,
                                                                    self.endpoint_type, self.endpoint_name)

                if endpoint is not None:
                    # Deletes the traffic manager and set change variable
                    endpoint = self.trafficmanager_client.endpoints.delete(self.resource_group, self.profile_name,
                                                                            self.endpoint_type, self.endpoint_name)
                    changed = True
                    results['status'] = 'Deleted'

        except CloudError:
            if self.state == 'present':
                changed = True

        self.results['changed'] = changed
        self.results['state'] = results

        if self.check_mode:
            return self.results

        return self.results

    def endpoint_to_dict(self, endpoint, resource_group, profile_name,
                            endpoint_type, endpoint_name, properties):

        '''
        Converts a traffic manager endpoint to a dictionary

        :param name: name of a traffic  manager endpoint
        :return: traffic manage object
        '''


    def create_or_update_traffic_manager_endpoints(self, resource_group, profile_name, endpoint_type, endpoint_name, parameters):
        '''
        Create or update a traffic manager endpoints.

        :param profile_name: name of a traffic  manager
        :return: traffic manage object
        '''

        target_resource_id = parameters.get('target_resource_id', None)
        target = parameters.get('target', None)
        endpoint_status = parameters.get('endpoint_status', None)
        weight = parameters.get('weight', None)
        priority = parameters.get('priority', None)
        endpoint_location = parameters.get('endpoint_location', None)
        endpoint_monitor_status = None
        min_child_endpoints = parameters.get('min_child_endpoints', None)
        geo_mapping = parameters.get('geo_mapping', None)

        endpoint_parameters = Endpoint(target_resource_id, target, endpoint_status, weight, priority, endpoint_location,
                                        endpoint_monitor_status, min_child_endpoints, geo_mapping)

        try:
            return self.trafficmanager_client.endpoints.create_or_update(resource_group, profile_name, endpoint_type, endpoint_name, endpoint_parameters)
        except CloudError as cloudError:
            self.fail("Error creating or updating traffic manager endpoints with name {0}.  {1}"
                      .format(endpoint_name, cloudError))
        except Exception as exc:
            self.fail("Error retrieving traffic manager {0} - {1}".format(profile_name, str(exc)))



def main():
    AzureRMTrafficManagerEndpoints()

if __name__ == '__main__':
    main()
