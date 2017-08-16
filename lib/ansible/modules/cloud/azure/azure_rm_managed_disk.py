#!/usr/bin/python
#
# Copyright (c) 2017 Bruno Medina Bolanos Cacho <bruno.medina@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_managed_disk

version_added: "2.4"

short_description: Manage Azure Manage Disks

description:
    - Create, update and delete an Azure Managed Disk

options:
    resource_group:
        description:
            - "Name of a resource group where the managed disk exists or will be created."
        required: true
    name:
        description:
            - Name of the managed disk
        required: true
    state:
        description:
            - Assert the state of the managed disk. Use 'present' to create or update a managed disk and
              'absent' to delete a managed disk.
        default: present
        choices:
            - absent
            - present
        required: false
    location:
        description:
            - Valid Azure location. Defaults to location of the resource group.
        default: resource_group location
        required: false
    storage_account_type:
        description:
            - "Type of storage for the managed disk: 'Standard_LRS'  or 'Premium_LRS'. If not specified the disk is created 'Standard_LRS'"
        choices:
            - Standard_LRS
            - Premium_LRS
        required: false
    create_option:
        description:
            - "Allowed values: empty, import, copy. 'import' from a VHD file in 'source_uri' and 'copy' from previous managed disk 'source_resource_id'."
        choices:
            - empty
            - import
            - copy
        required: false
    source_uri:
        description:
            - URI to a valid VHD file to be used when 'create_option' is 'import'.
        required: false
    source_resource_uri:
        description:
            - The resource ID of the managed disk to copy when 'create_option' is 'copy'.
        required: false
    os_type:
        description:
            - "Type of Operating System: 'linux' or 'windows'. Used when 'create_option' is either 'copy' or 'import' and the source is an OS disk."
        choices:
            - linux
            - windows
        required: false
    disk_size_gb:
        description:
            -Size in GB of the managed disk to be created. If 'create_option' is 'copy' then the value must be greater than or equal to the source's size.
        required: true
    tags:
        description:
            - Tags to assign to the managed disk.
        required: false

extends_documentation_fragment:
    - azure
    - azure_tags
author:
    - "Bruno Medina (@brusmx)"
'''

EXAMPLES = '''
    - name: Create managed disk
      azure_rm_managed_disk:
        name: mymanageddisk
        location: eastus
        resource_group: Testing
        disk_size_gb: 4

    - name: Delete managed disk
      azure_rm_manage_disk:
        name: mymanageddisk
        location: eastus
        resource_group: Testing
        state: absent
'''

RETURN = '''
id:
    description: The managed disk resource ID.
    returned: always
    type: dict
state:
    description: Current state of the managed disk
    returned: always
    type: dict
changed:
    description: Whether or not the resource has changed
    returned: always
    type: bool
'''

import re


from ansible.module_utils.azure_rm_common import AzureRMModuleBase
try:
    from msrestazure.azure_exceptions import CloudError
    from azure.common import AzureHttpError
    from azure.mgmt.compute.models import DiskCreateOption
except ImportError:
    # This is handled in azure_rm_common
    pass


def managed_disk_to_dict(managed_disk):
    return dict(
        id=managed_disk.id,
        name=managed_disk.name,
        type=managed_disk.type,
        location=managed_disk.location,
        tags=managed_disk.tags,
        time_created=managed_disk.tags,
        disk_size_gb=managed_disk.disk_size_gb,
        os_type=managed_disk.os_type,
        storage_account_type='Premium_LRS' if managed_disk.sku.tier == 'Premium' else 'Standard_LRS'
    )


class AzureRMManagedDisk(AzureRMModuleBase):
    """Configuration class for an Azure RM Managed Disk resource"""
    def __init__(self):
        self.module_arg_spec = dict(
            resource_group=dict(
                type='str',
                required=True
            ),
            name=dict(
                type='str',
                required=True
            ),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            location=dict(
                type='str',
                required=False
            ),
            storage_account_type=dict(
                type='str',
                required=False,
                choices=['Standard_LRS', 'Premium_LRS']
            ),
            create_option=dict(
                type='str',
                required=False,
                choices=['empty', 'import', 'copy']
            ),
            source_uri=dict(
                type='str',
                required=False
            ),
            source_resource_uri=dict(
                type='str',
                required=False
            ),
            os_type=dict(
                type='str',
                required=False,
                choices=['linux', 'windows']
            ),
            disk_size_gb=dict(
                type='int',
                required=True
            ),
            tags=dict(
                type='str',
                required=False
            ),
        )
        required_if = [
            ('create_option', 'import', ['source_uri']),
            ('create_option', 'copy', ['source_resource_uri'])
        ]
        self.results = dict(
            changed=False,
            state=dict())

        self.resource_group = None
        self.name = None
        self.location = None
        self.storage_account_type = None
        self.create_option = None
        self.source_uri = None
        self.source_resource_uri = None
        self.os_type = None
        self.disk_size_gb = None
        self.tags = None
        super(AzureRMManagedDisk, self).__init__(
            derived_arg_spec=self.module_arg_spec,
            required_if=required_if,
            supports_check_mode=True,
            supports_tags=True)

    def exec_module(self, **kwargs):
        """Main module execution method"""
        for key in list(self.module_arg_spec.keys()) + ['tags']:
            setattr(self, key, kwargs[key])
        results = dict()
        resource_group = None
        response = None
        try:
            resource_group = self.get_resource_group(self.resource_group)
        except CloudError:
            self.fail(
                'resource group {} not found'
                .format(self.resource_group))
        if not self.location:
            self.location = resource_group.location
        if self.state == 'present':
            self.results['state'] = self.create_or_update_managed_disk()
        elif self.state == 'absent':
            self.delete_managed_disk()
        return self.results

    def create_or_update_managed_disk(self):
        # Scaffolding empty managed disk
        disk_params = {}
        creation_data = {}
        disk_params['location'] = self.location
        disk_params['tags'] = self.tags
        if self.storage_account_type:
            disk_params['diskSku'] = self.storage_account_type
        disk_params['disk_size_gb'] = self.disk_size_gb
        # TODO: Add support for EncryptionSettings
        creation_data['create_option'] = DiskCreateOption.empty
        if self.create_option == 'import':
            creation_data['create_option'] = DiskCreateOption.import_enum
            creation_data['source_uri'] = self.source_uri
        elif self.create_option == 'copy':
            creation_data['create_option'] = DiskCreateOption.copy
            creation_data['source_resource_id'] = self.source_resource_id
        try:
            # CreationData cannot be changed after creation
            disk_params['creation_data'] = creation_data
            found_prev_disk = self.get_managed_disk()
            if self.is_different(found_prev_disk, disk_params):
                poller = self.compute_client.disks.create_or_update(
                    self.resource_group,
                    self.name,
                    disk_params)
                result = managed_disk_to_dict(self.get_poller_result(poller))
                self.results['changed'] = True
            else:
                result = found_prev_disk
                self.results['changed'] = False
        except AzureHttpError as e:
            self.fail("Error creating the managed disk: {0}".format(str(e)))
        return result

    def is_different(self, disk1, disk2):
        resp = False
        if disk2.get('disk_size_gb'):
            if not disk1['disk_size_gb'] == disk2['disk_size_gb']:
                resp = True
        if disk2.get('tags'):
            if not disk1['tags'] == disk2['tags']:
                resp = True
        if disk2.get('os_type'):
            if not disk1['os_type '] == disk2['os_type']:
                resp = True
        if disk2.get('storage_account_type'):
            if not disk1['storage_account_type'] == disk2['storage_account_type']:
                resp = True
        return resp

    def delete_managed_disk(self):
        try:
            poller = self.compute_client.disks.delete(
                self.resource_group,
                self.name)
            result = self.get_poller_result(poller)
        except AzureHttpError as e:
            self.fail("Error deleting the managed disk: {0}".format(str(e)))
        return result

    def get_managed_disk(self):
        found = False
        try:
            response = self.compute_client.disks.get(
                self.resource_group, 
                self.name)
            found = True
        except CloudError as e:
            self.log('Did not find managed disk')
        if found:
            return managed_disk_to_dict(response)
        else:
            return False


def main():
    """Main execution"""
    AzureRMManagedDisk()

if __name__ == '__main__':
    main()
