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

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ["preview"],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: gcp_dns_managed_zone
description:
    - A zone is a subtree of the DNS namespace under one administrative
      responsibility. A ManagedZone is a resource that represents a DNS zone
      hosted by the Cloud DNS service.
short_description: Creates a GCP ManagedZone
version_added: 2.5
author: Google Inc. (@googlecloudplatform)
requirements:
    - python >= 2.6
    - requests >= 2.18.4
    - google-auth >= 1.3.0
options:
    state:
        description:
            - Whether the given object should exist in GCP
        required: true
        choices: ['present', 'absent']
        default: 'present'
    description:
        description:
            - A mutable string of at most 1024 characters associated with this
              resource for the user's convenience. Has no effect on the managed
              zone's function.
        required: false
    dns_name:
        description:
            - The DNS name of this managed zone, for instance "example.com.".
        required: false
    name:
        description:
            - User assigned name for this resource.
              Must be unique within the project.
        required: true
    name_server_set:
        description:
            - Optionally specifies the NameServerSet for this ManagedZone. A
              NameServerSet is a set of DNS name servers that all host the same
              ManagedZones. Most users will leave this field unset.
        required: false
extends_documentation_fragment: gcp
'''

EXAMPLES = '''
- name: Create a Managed Zone
  gcp_dns_managed_zone:
      name: testObject
      dns_name: test.somewild2.example.com.
      description: 'test zone'
      project: testProject
      auth_kind: service_account
      service_account_file: /tmp/auth.pem
      scopes:
        - https://www.googleapis.com/auth/ndev.clouddns.readwrite
      state: 'present'
'''

RETURN = '''
    id:
        description:
            - Unique identifier for the resource; defined by the server.
        returned: success
        type: int
    name_servers:
        description:
            - Delegate your managed_zone to these virtual name servers;
              defined by the server
        returned: success
        type: list
    creation_time:
        description:
            - The time that this resource was created on the server.
              This is in RFC3339 text format.
        returned: success
        type: str
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequestException
import json

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            description=dict(type='str'),
            dns_name=dict(type='str'),
            name=dict(required=True, type='str'),
            name_server_set=dict(type='list'),
        )
    )

    state = module.params['state']
    kind = 'dns#managedZone'

    fetch = fetch_resource(module, self_link(module), kind)
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                fetch = update(module, self_link(module), kind)
        else:
            delete(module, self_link(module), kind)
            fetch = {}
            changed = True
    else:
        if state == 'present':
            fetch = create(module, collection(module), kind)
            changed = True

    if fetch:
        fetch.update({'changed': changed})
    else:
        fetch = {'changed': changed}

    module.exit_json(**fetch)


def create(module, link, kind):
    auth = GcpSession(module, 'g')
    return return_if_object(module, auth.post(link, resource_to_request(module)), kind)


def update(module, link, kind):
    module.fail_json(msg="ManagedZone cannot be edited")


def delete(module, link, kind):
    auth = GcpSession(module, 'g')
    return return_if_object(module, auth.delete(link), kind)


def resource_to_request(module):
    request = {
        u'kind': 'dns#managedZone',
        u'description': module.params['description'],
        u'dnsName': module.params['dns_name'],
        u'name': module.params['name'],
        u'nameServerSet': module.params['name_server_set'],
    }
    return_vals = {}
    for k, v in request.items():
        if v:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, kind):
    auth = GcpSession(module, 'g')
    return return_if_object(module, auth.get(link), kind)


def self_link(module):
    return "https://www.googleapis.com/dns/v1/projects/{project}/managedZones/{name}".format(**module.params)


def collection(module):
    return "https://www.googleapis.com/dns/v1/projects/{project}/managedZones".format(**module.params)


def return_if_object(module, response, kind):
    # If not found, return nothing.
    if response.status_code == 404:
        return None

    # If no content, return nothing.
    if response.status_code == 204:
        return None

    try:
        response.raise_for_status
        result = response.json()
    except getattr(json.decoder, 'JSONDecodeError', ValueError) as inst:
        module.fail_json(msg="Invalid JSON response with error: %s" % inst)
    except GcpRequestException as inst:
        module.fail_json(msg="Network error: %s" % inst)

    if navigate_hash(result, ['error', 'errors']):
        module.fail_json(msg=navigate_hash(result, ['error', 'errors']))
    if result['kind'] != kind:
        module.fail_json(msg="Incorrect result: {kind}".format(**result))

    return result


def is_different(module, response):
    request = resource_to_request(module)

    # Remove all output-only from response.
    return_vals = {}
    for k, v in response.items():
        if k in request:
            return_vals[k] = v

    return request != return_vals

if __name__ == '__main__':
    main()
