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
module: gcp_compute_target_tcp_proxy
description:
    - Represents a TargetTcpProxy resource, which is used by one or more global forwarding
      rule to route incoming TCP requests to a Backend service.
short_description: Creates a GCP TargetTcpProxy
version_added: 2.6
author: Google Inc. (@googlecloudplatform)
requirements:
    - python >= 2.6
    - requests >= 2.18.4
    - google-auth >= 1.3.0
options:
    state:
        description:
            - Whether the given object should exist in GCP
        choices: ['present', 'absent']
        default: 'present'
    description:
        description:
            - An optional description of this resource.
        required: false
    name:
        description:
            - Name of the resource. Provided by the client when the resource is created. The name
              must be 1-63 characters long, and comply with RFC1035. Specifically, the name must
              be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])?`
              which means the first character must be a lowercase letter, and all following characters
              must be a dash, lowercase letter, or digit, except the last character, which cannot
              be a dash.
        required: true
    proxy_header:
        description:
            - Specifies the type of proxy header to append before sending data to the backend,
              either NONE or PROXY_V1. The default is NONE.
        required: false
        choices: ['NONE', 'PROXY_V1']
    service:
        description:
            - A reference to the BackendService resource.
        required: true
extends_documentation_fragment: gcp
notes:
    - "API Reference: U(https://cloud.google.com/compute/docs/reference/latest/targetTcpProxies)"
    - "Setting Up TCP proxy for Google Cloud Load Balancing: U(https://cloud.google.com/compute/docs/load-balancing/tcp-ssl/tcp-proxy)"
'''

EXAMPLES = '''
- name: create a instance group
  gcp_compute_instance_group:
      name: "instancegroup-targettcpproxy"
      zone: us-central1-a
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      state: present
  register: instancegroup

- name: create a health check
  gcp_compute_health_check:
      name: "healthcheck-targettcpproxy"
      type: TCP
      tcp_health_check:
        port_name: service-health
        request: ping
        response: pong
      healthy_threshold: 10
      timeout_sec: 2
      unhealthy_threshold: 5
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      state: present
  register: healthcheck

- name: create a backend service
  gcp_compute_backend_service:
      name: "backendservice-targettcpproxy"
      backends:
      - group: "{{ instancegroup }}"
      health_checks:
      - "{{ healthcheck.selfLink }}"
      protocol: TCP
      project: "{{ gcp_project }}"
      auth_kind: "{{ gcp_cred_kind }}"
      service_account_file: "{{ gcp_cred_file }}"
      state: present
  register: backendservice

- name: create a target tcp proxy
  gcp_compute_target_tcp_proxy:
      name: "test_object"
      proxy_header: PROXY_V1
      service: "{{ backendservice }}"
      project: "test_project"
      auth_kind: "serviceaccount"
      service_account_file: "/tmp/auth.pem"
      state: present
'''

RETURN = '''
    creationTimestamp:
        description:
            - Creation timestamp in RFC3339 text format.
        returned: success
        type: str
    description:
        description:
            - An optional description of this resource.
        returned: success
        type: str
    id:
        description:
            - The unique identifier for the resource.
        returned: success
        type: int
    name:
        description:
            - Name of the resource. Provided by the client when the resource is created. The name
              must be 1-63 characters long, and comply with RFC1035. Specifically, the name must
              be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])?`
              which means the first character must be a lowercase letter, and all following characters
              must be a dash, lowercase letter, or digit, except the last character, which cannot
              be a dash.
        returned: success
        type: str
    proxyHeader:
        description:
            - Specifies the type of proxy header to append before sending data to the backend,
              either NONE or PROXY_V1. The default is NONE.
        returned: success
        type: str
    service:
        description:
            - A reference to the BackendService resource.
        returned: success
        type: dict
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, replace_resource_dict
import json
import time

################################################################################
# Main
################################################################################


def main():
    """Main function"""

    module = GcpModule(
        argument_spec=dict(
            state=dict(default='present', choices=['present', 'absent'], type='str'),
            description=dict(type='str'),
            name=dict(required=True, type='str'),
            proxy_header=dict(type='str', choices=['NONE', 'PROXY_V1']),
            service=dict(required=True, type='dict')
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    state = module.params['state']
    kind = 'compute#targetTcpProxy'

    fetch = fetch_resource(module, self_link(module), kind)
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                fetch = update(module, self_link(module), kind, fetch)
                changed = True
        else:
            delete(module, self_link(module), kind)
            fetch = {}
            changed = True
    else:
        if state == 'present':
            fetch = create(module, collection(module), kind)
            changed = True
        else:
            fetch = {}

    fetch.update({'changed': changed})

    module.exit_json(**fetch)


def create(module, link, kind):
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.post(link, resource_to_request(module)))


def update(module, link, kind, fetch):
    update_fields(module, resource_to_request(module),
                  response_to_hash(module, fetch))
    return fetch_resource(module, self_link(module), kind)


def update_fields(module, request, response):
    if response.get('proxyHeader') != request.get('proxyHeader'):
        proxy_header_update(module, request, response)
    if response.get('service') != request.get('service'):
        service_update(module, request, response)


def proxy_header_update(module, request, response):
    auth = GcpSession(module, 'compute')
    auth.post(
        ''.join([
            "https://www.googleapis.com/compute/v1/",
            "projects/{project}/global/targetTcpProxies/{name}/setProxyHeader"
        ]).format(**module.params),
        {
            u'proxyHeader': module.params.get('proxy_header')
        }
    )


def service_update(module, request, response):
    auth = GcpSession(module, 'compute')
    auth.post(
        ''.join([
            "https://www.googleapis.com/compute/v1/",
            "projects/{project}/global/targetTcpProxies/{name}/setBackendService"
        ]).format(**module.params),
        {
            u'service': replace_resource_dict(module.params.get(u'service', {}), 'selfLink')
        }
    )


def delete(module, link, kind):
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'kind': 'compute#targetTcpProxy',
        u'description': module.params.get('description'),
        u'name': module.params.get('name'),
        u'proxyHeader': module.params.get('proxy_header'),
        u'service': replace_resource_dict(module.params.get(u'service', {}), 'selfLink')
    }
    return_vals = {}
    for k, v in request.items():
        if v:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, kind, allow_not_found=True):
    auth = GcpSession(module, 'compute')
    return return_if_object(module, auth.get(link), kind, allow_not_found)


def self_link(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/global/targetTcpProxies/{name}".format(**module.params)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/global/targetTcpProxies".format(**module.params)


def return_if_object(module, response, kind, allow_not_found=False):
    # If not found, return nothing.
    if allow_not_found and response.status_code == 404:
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
        u'creationTimestamp': response.get(u'creationTimestamp'),
        u'description': module.params.get('description'),
        u'id': response.get(u'id'),
        u'name': module.params.get('name'),
        u'proxyHeader': response.get(u'proxyHeader'),
        u'service': response.get(u'service')
    }


def async_op_url(module, extra_data=None):
    if extra_data is None:
        extra_data = {}
    url = "https://www.googleapis.com/compute/v1/projects/{project}/global/operations/{op_id}"
    combined = extra_data.copy()
    combined.update(module.params)
    return url.format(**combined)


def wait_for_operation(module, response):
    op_result = return_if_object(module, response, 'compute#operation')
    if op_result is None:
        return {}
    status = navigate_hash(op_result, ['status'])
    wait_done = wait_for_completion(status, op_result, module)
    return fetch_resource(module, navigate_hash(wait_done, ['targetLink']), 'compute#targetTcpProxy')


def wait_for_completion(status, op_result, module):
    op_id = navigate_hash(op_result, ['name'])
    op_uri = async_op_url(module, {'op_id': op_id})
    while status != 'DONE':
        raise_if_errors(op_result, ['error', 'errors'], 'message')
        time.sleep(1.0)
        if status not in ['PENDING', 'RUNNING', 'DONE']:
            module.fail_json(msg="Invalid result %s" % status)
        op_result = fetch_resource(module, op_uri, 'compute#operation')
        status = navigate_hash(op_result, ['status'])
    return op_result


def raise_if_errors(response, err_path, module):
    errors = navigate_hash(response, err_path)
    if errors is not None:
        module.fail_json(msg=errors)


if __name__ == '__main__':
    main()
