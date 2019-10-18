#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2017 Google
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
# ----------------------------------------------------------------------------
#
#     ***     AUTO GENERATED CODE    ***    AUTO GENERATED CODE     ***
#
# ----------------------------------------------------------------------------
#
#     This file is automatically generated by Magic Modules and manual
#     changes will be clobbered when the file is regenerated.
#
#     Please read more about how to change this file at
#     https://www.github.com/GoogleCloudPlatform/magic-modules
#
# ----------------------------------------------------------------------------

from __future__ import absolute_import, division, print_function

__metaclass__ = type

################################################################################
# Documentation
################################################################################

ANSIBLE_METADATA = {'metadata_version': '1.1', 'status': ["preview"], 'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_filestore_instance
description:
- A Google Cloud Filestore instance.
short_description: Creates a GCP Instance
version_added: '2.9'
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  state:
    description:
    - Whether the given object should exist in GCP
    choices:
    - present
    - absent
    default: present
    type: str
  name:
    description:
    - The resource name of the instance.
    required: true
    type: str
  description:
    description:
    - A description of the instance.
    required: false
    type: str
  tier:
    description:
    - The service tier of the instance.
    - 'Some valid choices include: "TIER_UNSPECIFIED", "STANDARD", "PREMIUM"'
    required: true
    type: str
  labels:
    description:
    - Resource labels to represent user-provided metadata.
    required: false
    type: dict
  file_shares:
    description:
    - File system shares on the instance. For this version, only a single file share
      is supported.
    required: true
    type: list
    suboptions:
      name:
        description:
        - The name of the fileshare (16 characters or less) .
        required: true
        type: str
      capacity_gb:
        description:
        - File share capacity in GiB. This must be at least 1024 GiB for the standard
          tier, or 2560 GiB for the premium tier.
        required: true
        type: int
  networks:
    description:
    - VPC networks to which the instance is connected. For this version, only a single
      network is supported.
    required: true
    type: list
    suboptions:
      network:
        description:
        - The name of the GCE VPC network to which the instance is connected.
        required: true
        type: str
      modes:
        description:
        - IP versions for which the instance has IP addresses assigned.
        required: true
        type: list
      reserved_ip_range:
        description:
        - A /29 CIDR block that identifies the range of IP addresses reserved for
          this instance.
        required: false
        type: str
  zone:
    description:
    - The name of the Filestore zone of the instance.
    required: true
    type: str
  project:
    description:
    - The Google Cloud Platform project to use.
    type: str
  auth_kind:
    description:
    - The type of credential used.
    type: str
    required: true
    choices:
    - application
    - machineaccount
    - serviceaccount
  service_account_contents:
    description:
    - The contents of a Service Account JSON file, either in a dictionary or as a
      JSON string that represents it.
    type: jsonarg
  service_account_file:
    description:
    - The path of a Service Account JSON file if serviceaccount is selected as type.
    type: path
  service_account_email:
    description:
    - An optional service account email address if machineaccount is selected and
      the user does not wish to use the default email.
    type: str
  scopes:
    description:
    - Array of scopes to be used
    type: list
  env_type:
    description:
    - Specifies which Ansible environment you're running this module within.
    - This should not be set unless you know what you're doing.
    - This only alters the User Agent string for any API requests.
    type: str
notes:
- 'API Reference: U(https://cloud.google.com/filestore/docs/reference/rest/v1beta1/projects.locations.instances/create)'
- 'Official Documentation: U(https://cloud.google.com/filestore/docs/creating-instances)'
- 'Use with Kubernetes: U(https://cloud.google.com/filestore/docs/accessing-fileshares)'
- 'Copying Data In/Out: U(https://cloud.google.com/filestore/docs/copying-data)'
- for authentication, you can set service_account_file using the c(gcp_service_account_file)
  env variable.
- for authentication, you can set service_account_contents using the c(GCP_SERVICE_ACCOUNT_CONTENTS)
  env variable.
- For authentication, you can set service_account_email using the C(GCP_SERVICE_ACCOUNT_EMAIL)
  env variable.
- For authentication, you can set auth_kind using the C(GCP_AUTH_KIND) env variable.
- For authentication, you can set scopes using the C(GCP_SCOPES) env variable.
- Environment variables values will only be used if the playbook values are not set.
- The I(service_account_email) and I(service_account_file) options are mutually exclusive.
'''

EXAMPLES = '''
- name: create a instance
  gcp_filestore_instance:
    name: test_object
    zone: us-central1-b
    tier: PREMIUM
    file_shares:
    - capacity_gb: 2660
      name: share1
    networks:
    - network: default
      modes:
      - MODE_IPV4
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
    state: present
'''

RETURN = '''
name:
  description:
  - The resource name of the instance.
  returned: success
  type: str
description:
  description:
  - A description of the instance.
  returned: success
  type: str
createTime:
  description:
  - Creation timestamp in RFC3339 text format.
  returned: success
  type: str
tier:
  description:
  - The service tier of the instance.
  returned: success
  type: str
labels:
  description:
  - Resource labels to represent user-provided metadata.
  returned: success
  type: dict
fileShares:
  description:
  - File system shares on the instance. For this version, only a single file share
    is supported.
  returned: success
  type: complex
  contains:
    name:
      description:
      - The name of the fileshare (16 characters or less) .
      returned: success
      type: str
    capacityGb:
      description:
      - File share capacity in GiB. This must be at least 1024 GiB for the standard
        tier, or 2560 GiB for the premium tier.
      returned: success
      type: int
networks:
  description:
  - VPC networks to which the instance is connected. For this version, only a single
    network is supported.
  returned: success
  type: complex
  contains:
    network:
      description:
      - The name of the GCE VPC network to which the instance is connected.
      returned: success
      type: str
    modes:
      description:
      - IP versions for which the instance has IP addresses assigned.
      returned: success
      type: list
    reservedIpRange:
      description:
      - A /29 CIDR block that identifies the range of IP addresses reserved for this
        instance.
      returned: success
      type: str
    ipAddresses:
      description:
      - A list of IPv4 or IPv6 addresses.
      returned: success
      type: list
etag:
  description:
  - Server-specified ETag for the instance resource to prevent simultaneous updates
    from overwriting each other.
  returned: success
  type: str
zone:
  description:
  - The name of the Filestore zone of the instance.
  returned: success
  type: str
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, remove_nones_from_dict, replace_resource_dict
import json
import re
import time

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            name=dict(required=True, type='str'),
            description=dict(type='str'),
            tier=dict(required=True, type='str'),
            labels=dict(type='dict'),
            file_shares=dict(
                required=True, type='list', elements='dict', options=dict(name=dict(required=True, type='str'), capacity_gb=dict(required=True, type='int'))
            ),
            networks=dict(
                required=True,
                type='list',
                elements='dict',
                options=dict(
                    network=dict(required=True, type='str'), modes=dict(required=True, type='list', elements='str'), reserved_ip_range=dict(type='str')
                ),
            ),
            zone=dict(required=True, type='str'),
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/cloud-platform']

    state = module.params['state']

    fetch = fetch_resource(module, self_link(module))
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                update(module, self_link(module), fetch)
                fetch = fetch_resource(module, self_link(module))
                changed = True
        else:
            delete(module, self_link(module))
            fetch = {}
            changed = True
    else:
        if state == 'present':
            fetch = create(module, create_link(module))
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(module, link):
    auth = GcpSession(module, 'filestore')
    return wait_for_operation(module, auth.post(link, resource_to_request(module)))


def update(module, link, fetch):
    auth = GcpSession(module, 'filestore')
    params = {'updateMask': updateMask(resource_to_request(module), response_to_hash(module, fetch))}
    request = resource_to_request(module)
    return wait_for_operation(module, auth.patch(link, request, params=params))


def updateMask(request, response):
    update_mask = []
    if request.get('description') != response.get('description'):
        update_mask.append('description')
    if request.get('labels') != response.get('labels'):
        update_mask.append('labels')
    if request.get('fileShares') != response.get('fileShares'):
        update_mask.append('fileShares')
    return ','.join(update_mask)


def delete(module, link):
    auth = GcpSession(module, 'filestore')
    return wait_for_operation(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'description': module.params.get('description'),
        u'tier': module.params.get('tier'),
        u'labels': module.params.get('labels'),
        u'fileShares': InstanceFilesharesArray(module.params.get('file_shares', []), module).to_request(),
        u'networks': InstanceNetworksArray(module.params.get('networks', []), module).to_request(),
    }
    return_vals = {}
    for k, v in request.items():
        if v or v is False:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, allow_not_found=True):
    auth = GcpSession(module, 'filestore')
    return return_if_object(module, auth.get(link), allow_not_found)


def self_link(module):
    return "https://file.googleapis.com/v1/projects/{project}/locations/{zone}/instances/{name}".format(**module.params)


def collection(module):
    return "https://file.googleapis.com/v1/projects/{project}/locations/{zone}/instances".format(**module.params)


def create_link(module):
    return "https://file.googleapis.com/v1/projects/{project}/locations/{zone}/instances?instanceId={name}".format(**module.params)


def return_if_object(module, response, allow_not_found=False):
    # If not found, return nothing.
    if allow_not_found and response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError):
        module.fail_json(msg="Invalid JSON response with error: %s" % response.text)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


def is_different(module, response):
    request = resource_to_request(module)
    response = response_to_hash(module, response)

    # Remove all output-only from response.
    response_vals = {}
    for k, v in response.items():
        if k in request:
            response_vals[k] = v

    request_vals = {}
    for k, v in request.items():
        if k in response:
            request_vals[k] = v

    return GcpRequest(request_vals) != GcpRequest(response_vals)


# Remove unnecessary properties from the response.
# This is for doing comparisons with Ansible's current parameters.
def response_to_hash(module, response):
    return {
        u'name': response.get(u'name'),
        u'description': response.get(u'description'),
        u'createTime': response.get(u'createTime'),
        u'tier': module.params.get('tier'),
        u'labels': response.get(u'labels'),
        u'fileShares': InstanceFilesharesArray(response.get(u'fileShares', []), module).from_response(),
        u'networks': InstanceNetworksArray(module.params.get('networks', []), module).to_request(),
        u'etag': response.get(u'etag'),
    }


def name_pattern(name, module):
    if name is None:
        return

    regex = r"projects/.*/locations/.*/instances/.*"

    if not re.match(regex, name):
        name = "projects/{project}/locations/{zone}/instances/{name}".format(**module.params)

    return name


def async_op_url(module, extra_data=None):
    if extra_data is None:
        extra_data = {}
    url = "https://file.googleapis.com/v1/{op_id}"
    combined = extra_data.copy()
    combined.update(module.params)
    return url.format(**combined)


def wait_for_operation(module, response):
    op_result = return_if_object(module, response)
    if op_result is None:
        return {}
    status = navigate_hash(op_result, ['done'])
    wait_done = wait_for_completion(status, op_result, module)
    raise_if_errors(wait_done, ['error'], module)
    return navigate_hash(wait_done, ['response'])


def wait_for_completion(status, op_result, module):
    op_id = navigate_hash(op_result, ['name'])
    op_uri = async_op_url(module, {'op_id': op_id})
    while not status:
        raise_if_errors(op_result, ['error'], module)
        time.sleep(1.0)
        op_result = fetch_resource(module, op_uri, False)
        status = navigate_hash(op_result, ['done'])
    return op_result


def raise_if_errors(response, err_path, module):
    errors = navigate_hash(response, err_path)
    if errors is not None:
        module.fail_json(msg=errors)


class InstanceFilesharesArray(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = []

    def to_request(self):
        items = []
        for item in self.request:
            items.append(self._request_for_item(item))
        return items

    def from_response(self):
        items = []
        for item in self.request:
            items.append(self._response_from_item(item))
        return items

    def _request_for_item(self, item):
        return remove_nones_from_dict({u'name': item.get('name'), u'capacityGb': item.get('capacity_gb')})

    def _response_from_item(self, item):
        return remove_nones_from_dict({u'name': item.get(u'name'), u'capacityGb': item.get(u'capacityGb')})


class InstanceNetworksArray(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = []

    def to_request(self):
        items = []
        for item in self.request:
            items.append(self._request_for_item(item))
        return items

    def from_response(self):
        items = []
        for item in self.request:
            items.append(self._response_from_item(item))
        return items

    def _request_for_item(self, item):
        return remove_nones_from_dict({u'network': item.get('network'), u'modes': item.get('modes'), u'reservedIpRange': item.get('reserved_ip_range')})

    def _response_from_item(self, item):
        return remove_nones_from_dict(
            {u'network': self.module.params.get('network'), u'modes': self.module.params.get('modes'), u'reservedIpRange': item.get(u'reservedIpRange')}
        )


if __name__ == '__main__':
    main()
