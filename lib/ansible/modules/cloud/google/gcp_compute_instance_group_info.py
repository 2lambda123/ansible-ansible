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
module: gcp_compute_instance_group_info
description:
- Gather info for GCP InstanceGroup
- This module was called C({{ old_name }}) before Ansible 2.9. The usage has not changed.
short_description: Gather info for GCP InstanceGroup
version_added: 2.7
author: Google Inc. (@googlecloudplatform)
requirements:
- python >= 2.6
- requests >= 2.18.4
- google-auth >= 1.3.0
options:
  filters:
    description:
    - A list of filter value pairs. Available filters are listed here U(https://cloud.google.com/sdk/gcloud/reference/topic/filters).
    - Each additional filter in the list will act be added as an AND condition (filter1
      and filter2) .
    type: list
  zone:
    description:
    - A reference to the zone where the instance group resides.
    required: true
    type: str
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: get info on a instance group info
  gcp_compute_instance_group_info:
    zone: us-central1-a
    filters:
    - name = test_object
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
'''

RETURN = '''
resources:
  description: List of resources
  returned: always
  type: complex
  contains:
    creationTimestamp:
      description:
      - Creation timestamp in RFC3339 text format.
      returned: success
      type: str
    description:
      description:
      - An optional description of this resource. Provide this property when you create
        the resource.
      returned: success
      type: str
    id:
      description:
      - A unique identifier for this instance group.
      returned: success
      type: int
    name:
      description:
      - The name of the instance group.
      - The name must be 1-63 characters long, and comply with RFC1035.
      returned: success
      type: str
    namedPorts:
      description:
      - Assigns a name to a port number.
      - 'For example: {name: "http", port: 80}.'
      - This allows the system to reference ports by the assigned name instead of
        a port number. Named ports can also contain multiple ports.
      - 'For example: [{name: "http", port: 80},{name: "http", port: 8080}] Named
        ports apply to all instances in this instance group.'
      returned: success
      type: complex
      contains:
        name:
          description:
          - The name for this named port.
          - The name must be 1-63 characters long, and comply with RFC1035.
          returned: success
          type: str
        port:
          description:
          - The port number, which can be a value between 1 and 65535.
          returned: success
          type: int
    network:
      description:
      - The network to which all instances in the instance group belong.
      returned: success
      type: dict
    region:
      description:
      - The region where the instance group is located (for regional resources).
      returned: success
      type: str
    subnetwork:
      description:
      - The subnetwork to which all instances in the instance group belong.
      returned: success
      type: dict
    zone:
      description:
      - A reference to the zone where the instance group resides.
      returned: success
      type: str
    instances:
      description:
      - The list of instances associated with this InstanceGroup.
      - All instances must be created before being added to an InstanceGroup.
      - All instances not in this list will be removed from the InstanceGroup and
        will not be deleted.
      - Only the full identifier of the instance will be returned.
      returned: success
      type: list
'''

################################################################################
# Imports
################################################################################
from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest
import json

################################################################################
# Main
################################################################################


def main():
    module = GcpModule(argument_spec=dict(filters=dict(type='list', elements='str'), zone=dict(required=True, type='str')))

    if module._name == 'gcp_compute_instance_group_facts':
        module.deprecate("The 'gcp_compute_instance_group_facts' module has been renamed to 'gcp_compute_instance_group_info'", version='2.13')

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    items = fetch_list(module, collection(module), query_options(module.params['filters']))
    if items.get('items'):
        items = items.get('items')
    else:
        items = []
    return_value = {'resources': items}
    module.exit_json(**return_value)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/zones/{zone}/instanceGroups".format(**module.params)


def fetch_list(module, link, query):
    auth = GcpSession(module, 'compute')
    response = auth.get(link, params={'filter': query})
    return return_if_object(module, response)


def query_options(filters):
    if not filters:
        return ''

    if len(filters) == 1:
        return filters[0]
    else:
        queries = []
        for f in filters:
            # For multiple queries, all queries should have ()
            if f[0] != '(' and f[-1] != ')':
                queries.append("(%s)" % ''.join(f))
            else:
                queries.append(f)

        return ' '.join(queries)


def return_if_object(module, response):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        module.raise_for_status(response)
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))

    return result


if __name__ == "__main__":
    main()
