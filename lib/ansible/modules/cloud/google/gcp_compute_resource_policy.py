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
module: gcp_compute_resource_policy
description:
- A policy that can be attached to a resource to specify or schedule actions on that
  resource.
short_description: Creates a GCP ResourcePolicy
version_added: '2.10'
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
    - The name of the resource, provided by the client when initially creating the
      resource. The resource name must be 1-63 characters long, and comply with RFC1035.
      Specifically, the name must be 1-63 characters long and match the regular expression
      `[a-z]([-a-z0-9]*[a-z0-9])`? which means the first character must be a lowercase
      letter, and all following characters must be a dash, lowercase letter, or digit,
      except the last character, which cannot be a dash.
    required: true
    type: str
  snapshot_schedule_policy:
    description:
    - Policy for creating snapshots of persistent disks.
    required: false
    type: dict
    suboptions:
      schedule:
        description:
        - Contains one of an `hourlySchedule`, `dailySchedule`, or `weeklySchedule`.
        required: true
        type: dict
        suboptions:
          hourly_schedule:
            description:
            - The policy will execute every nth hour starting at the specified time.
            required: false
            type: dict
            suboptions:
              hours_in_cycle:
                description:
                - The number of hours between snapshots.
                required: true
                type: int
              start_time:
                description:
                - Time within the window to start the operations.
                - 'It must be in an hourly format "HH:MM", where HH : [00-23] and
                  MM : [00] GMT.'
                - 'eg: 21:00 .'
                required: true
                type: str
          daily_schedule:
            description:
            - The policy will execute every nth day at the specified time.
            required: false
            type: dict
            suboptions:
              days_in_cycle:
                description:
                - The number of days between snapshots.
                required: true
                type: int
              start_time:
                description:
                - This must be in UTC format that resolves to one of 00:00, 04:00,
                  08:00, 12:00, 16:00, or 20:00. For example, both 13:00-5 and 08:00
                  are valid.
                required: true
                type: str
          weekly_schedule:
            description:
            - Allows specifying a snapshot time for each day of the week.
            required: false
            type: dict
            suboptions:
              day_of_weeks:
                description:
                - May contain up to seven (one for each day of the week) snapshot
                  times.
                elements: dict
                required: true
                type: list
                suboptions:
                  start_time:
                    description:
                    - Time within the window to start the operations.
                    - 'It must be in format "HH:MM", where HH : [00-23] and MM : [00-00]
                      GMT.'
                    required: true
                    type: str
                  day:
                    description:
                    - The day of the week to create the snapshot. e.g. MONDAY .
                    - 'Some valid choices include: "MONDAY", "TUESDAY", "WEDNESDAY",
                      "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"'
                    required: true
                    type: str
      retention_policy:
        description:
        - Retention policy applied to snapshots created by this resource policy.
        required: false
        type: dict
        suboptions:
          max_retention_days:
            description:
            - Maximum age of the snapshot that is allowed to be kept.
            required: true
            type: int
          on_source_disk_delete:
            description:
            - Specifies the behavior to apply to scheduled snapshots when the source
              disk is deleted.
            - Valid options are KEEP_AUTO_SNAPSHOTS and APPLY_RETENTION_POLICY .
            - 'Some valid choices include: "KEEP_AUTO_SNAPSHOTS", "APPLY_RETENTION_POLICY"'
            required: false
            default: KEEP_AUTO_SNAPSHOTS
            type: str
      snapshot_properties:
        description:
        - Properties with which the snapshots are created, such as labels.
        required: false
        type: dict
        suboptions:
          labels:
            description:
            - A set of key-value pairs.
            required: false
            type: dict
          storage_locations:
            description:
            - Cloud Storage bucket location to store the auto snapshot (regional or
              multi-regional) .
            elements: str
            required: false
            type: list
          guest_flush:
            description:
            - Whether to perform a 'guest aware' snapshot.
            required: false
            type: bool
  region:
    description:
    - Region where resource policy resides.
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
'''

EXAMPLES = '''
- name: create a resource policy
  gcp_compute_resource_policy:
    name: test_object
    region: us-central1
    snapshot_schedule_policy:
      schedule:
        daily_schedule:
          days_in_cycle: 1
          start_time: '04:00'
    project: test_project
    auth_kind: serviceaccount
    service_account_file: "/tmp/auth.pem"
    state: present
'''

RETURN = '''
name:
  description:
  - The name of the resource, provided by the client when initially creating the resource.
    The resource name must be 1-63 characters long, and comply with RFC1035. Specifically,
    the name must be 1-63 characters long and match the regular expression `[a-z]([-a-z0-9]*[a-z0-9])`?
    which means the first character must be a lowercase letter, and all following
    characters must be a dash, lowercase letter, or digit, except the last character,
    which cannot be a dash.
  returned: success
  type: str
snapshotSchedulePolicy:
  description:
  - Policy for creating snapshots of persistent disks.
  returned: success
  type: complex
  contains:
    schedule:
      description:
      - Contains one of an `hourlySchedule`, `dailySchedule`, or `weeklySchedule`.
      returned: success
      type: complex
      contains:
        hourlySchedule:
          description:
          - The policy will execute every nth hour starting at the specified time.
          returned: success
          type: complex
          contains:
            hoursInCycle:
              description:
              - The number of hours between snapshots.
              returned: success
              type: int
            startTime:
              description:
              - Time within the window to start the operations.
              - 'It must be in an hourly format "HH:MM", where HH : [00-23] and MM
                : [00] GMT.'
              - 'eg: 21:00 .'
              returned: success
              type: str
        dailySchedule:
          description:
          - The policy will execute every nth day at the specified time.
          returned: success
          type: complex
          contains:
            daysInCycle:
              description:
              - The number of days between snapshots.
              returned: success
              type: int
            startTime:
              description:
              - This must be in UTC format that resolves to one of 00:00, 04:00, 08:00,
                12:00, 16:00, or 20:00. For example, both 13:00-5 and 08:00 are valid.
              returned: success
              type: str
        weeklySchedule:
          description:
          - Allows specifying a snapshot time for each day of the week.
          returned: success
          type: complex
          contains:
            dayOfWeeks:
              description:
              - May contain up to seven (one for each day of the week) snapshot times.
              returned: success
              type: complex
              contains:
                startTime:
                  description:
                  - Time within the window to start the operations.
                  - 'It must be in format "HH:MM", where HH : [00-23] and MM : [00-00]
                    GMT.'
                  returned: success
                  type: str
                day:
                  description:
                  - The day of the week to create the snapshot. e.g. MONDAY .
                  returned: success
                  type: str
    retentionPolicy:
      description:
      - Retention policy applied to snapshots created by this resource policy.
      returned: success
      type: complex
      contains:
        maxRetentionDays:
          description:
          - Maximum age of the snapshot that is allowed to be kept.
          returned: success
          type: int
        onSourceDiskDelete:
          description:
          - Specifies the behavior to apply to scheduled snapshots when the source
            disk is deleted.
          - Valid options are KEEP_AUTO_SNAPSHOTS and APPLY_RETENTION_POLICY .
          returned: success
          type: str
    snapshotProperties:
      description:
      - Properties with which the snapshots are created, such as labels.
      returned: success
      type: complex
      contains:
        labels:
          description:
          - A set of key-value pairs.
          returned: success
          type: dict
        storageLocations:
          description:
          - Cloud Storage bucket location to store the auto snapshot (regional or
            multi-regional) .
          returned: success
          type: list
        guestFlush:
          description:
          - Whether to perform a 'guest aware' snapshot.
          returned: success
          type: bool
region:
  description:
  - Region where resource policy resides.
  returned: success
  type: str
'''

################################################################################
# Imports
################################################################################

from ansible.module_utils.gcp_utils import navigate_hash, GcpSession, GcpModule, GcpRequest, remove_nones_from_dict, replace_resource_dict
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
            name=dict(required=True, type='str'),
            snapshot_schedule_policy=dict(
                type='dict',
                options=dict(
                    schedule=dict(
                        required=True,
                        type='dict',
                        options=dict(
                            hourly_schedule=dict(
                                type='dict', options=dict(hours_in_cycle=dict(required=True, type='int'), start_time=dict(required=True, type='str'))
                            ),
                            daily_schedule=dict(
                                type='dict', options=dict(days_in_cycle=dict(required=True, type='int'), start_time=dict(required=True, type='str'))
                            ),
                            weekly_schedule=dict(
                                type='dict',
                                options=dict(
                                    day_of_weeks=dict(
                                        required=True,
                                        type='list',
                                        elements='dict',
                                        options=dict(start_time=dict(required=True, type='str'), day=dict(required=True, type='str')),
                                    )
                                ),
                            ),
                        ),
                    ),
                    retention_policy=dict(
                        type='dict',
                        options=dict(max_retention_days=dict(required=True, type='int'), on_source_disk_delete=dict(default='KEEP_AUTO_SNAPSHOTS', type='str')),
                    ),
                    snapshot_properties=dict(
                        type='dict', options=dict(labels=dict(type='dict'), storage_locations=dict(type='list', elements='str'), guest_flush=dict(type='bool'))
                    ),
                ),
            ),
            region=dict(required=True, type='str'),
        )
    )

    if not module.params['scopes']:
        module.params['scopes'] = ['https://www.googleapis.com/auth/compute']

    state = module.params['state']
    kind = 'compute#resourcePolicy'

    fetch = fetch_resource(module, self_link(module), kind)
    changed = False

    if fetch:
        if state == 'present':
            if is_different(module, fetch):
                update(module, self_link(module), kind)
                fetch = fetch_resource(module, self_link(module), kind)
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


def update(module, link, kind):
    delete(module, self_link(module), kind)
    create(module, collection(module), kind)


def delete(module, link, kind):
    auth = GcpSession(module, 'compute')
    return wait_for_operation(module, auth.delete(link))


def resource_to_request(module):
    request = {
        u'kind': 'compute#resourcePolicy',
        u'region': module.params.get('region'),
        u'name': module.params.get('name'),
        u'snapshotSchedulePolicy': ResourcePolicySnapshotschedulepolicy(module.params.get('snapshot_schedule_policy', {}), module).to_request(),
    }
    return_vals = {}
    for k, v in request.items():
        if v or v is False:
            return_vals[k] = v

    return return_vals


def fetch_resource(module, link, kind, allow_not_found=True):
    auth = GcpSession(module, 'compute')
    return return_if_object(module, auth.get(link), kind, allow_not_found)


def self_link(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/resourcePolicies/{name}".format(**module.params)


def collection(module):
    return "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/resourcePolicies".format(**module.params)


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
        u'snapshotSchedulePolicy': ResourcePolicySnapshotschedulepolicy(response.get(u'snapshotSchedulePolicy', {}), module).from_response(),
    }


def async_op_url(module, extra_data=None):
    if extra_data is None:
        extra_data = {}
    url = "https://www.googleapis.com/compute/v1/projects/{project}/regions/{region}/operations/{op_id}"
    combined = extra_data.copy()
    combined.update(module.params)
    return url.format(**combined)


def wait_for_operation(module, response):
    op_result = return_if_object(module, response, 'compute#operation')
    if op_result is None:
        return {}
    status = navigate_hash(op_result, ['status'])
    wait_done = wait_for_completion(status, op_result, module)
    return fetch_resource(module, navigate_hash(wait_done, ['targetLink']), 'compute#resourcePolicy')


def wait_for_completion(status, op_result, module):
    op_id = navigate_hash(op_result, ['name'])
    op_uri = async_op_url(module, {'op_id': op_id})
    while status != 'DONE':
        raise_if_errors(op_result, ['error', 'errors'], module)
        time.sleep(1.0)
        op_result = fetch_resource(module, op_uri, 'compute#operation', False)
        status = navigate_hash(op_result, ['status'])
    return op_result


def raise_if_errors(response, err_path, module):
    errors = navigate_hash(response, err_path)
    if errors is not None:
        module.fail_json(msg=errors)


class ResourcePolicySnapshotschedulepolicy(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict(
            {
                u'schedule': ResourcePolicySchedule(self.request.get('schedule', {}), self.module).to_request(),
                u'retentionPolicy': ResourcePolicyRetentionpolicy(self.request.get('retention_policy', {}), self.module).to_request(),
                u'snapshotProperties': ResourcePolicySnapshotproperties(self.request.get('snapshot_properties', {}), self.module).to_request(),
            }
        )

    def from_response(self):
        return remove_nones_from_dict(
            {
                u'schedule': ResourcePolicySchedule(self.request.get(u'schedule', {}), self.module).from_response(),
                u'retentionPolicy': ResourcePolicyRetentionpolicy(self.request.get(u'retentionPolicy', {}), self.module).from_response(),
                u'snapshotProperties': ResourcePolicySnapshotproperties(self.request.get(u'snapshotProperties', {}), self.module).from_response(),
            }
        )


class ResourcePolicySchedule(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict(
            {
                u'hourlySchedule': ResourcePolicyHourlyschedule(self.request.get('hourly_schedule', {}), self.module).to_request(),
                u'dailySchedule': ResourcePolicyDailyschedule(self.request.get('daily_schedule', {}), self.module).to_request(),
                u'weeklySchedule': ResourcePolicyWeeklyschedule(self.request.get('weekly_schedule', {}), self.module).to_request(),
            }
        )

    def from_response(self):
        return remove_nones_from_dict(
            {
                u'hourlySchedule': ResourcePolicyHourlyschedule(self.request.get(u'hourlySchedule', {}), self.module).from_response(),
                u'dailySchedule': ResourcePolicyDailyschedule(self.request.get(u'dailySchedule', {}), self.module).from_response(),
                u'weeklySchedule': ResourcePolicyWeeklyschedule(self.request.get(u'weeklySchedule', {}), self.module).from_response(),
            }
        )


class ResourcePolicyHourlyschedule(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict({u'hoursInCycle': self.request.get('hours_in_cycle'), u'startTime': self.request.get('start_time')})

    def from_response(self):
        return remove_nones_from_dict({u'hoursInCycle': self.request.get(u'hoursInCycle'), u'startTime': self.request.get(u'startTime')})


class ResourcePolicyDailyschedule(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict({u'daysInCycle': self.request.get('days_in_cycle'), u'startTime': self.request.get('start_time')})

    def from_response(self):
        return remove_nones_from_dict({u'daysInCycle': self.request.get(u'daysInCycle'), u'startTime': self.request.get(u'startTime')})


class ResourcePolicyWeeklyschedule(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict({u'dayOfWeeks': ResourcePolicyDayofweeksArray(self.request.get('day_of_weeks', []), self.module).to_request()})

    def from_response(self):
        return remove_nones_from_dict({u'dayOfWeeks': ResourcePolicyDayofweeksArray(self.request.get(u'dayOfWeeks', []), self.module).from_response()})


class ResourcePolicyDayofweeksArray(object):
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
        return remove_nones_from_dict({u'startTime': item.get('start_time'), u'day': item.get('day')})

    def _response_from_item(self, item):
        return remove_nones_from_dict({u'startTime': item.get(u'startTime'), u'day': item.get(u'day')})


class ResourcePolicyRetentionpolicy(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict(
            {u'maxRetentionDays': self.request.get('max_retention_days'), u'onSourceDiskDelete': self.request.get('on_source_disk_delete')}
        )

    def from_response(self):
        return remove_nones_from_dict(
            {u'maxRetentionDays': self.request.get(u'maxRetentionDays'), u'onSourceDiskDelete': self.request.get(u'onSourceDiskDelete')}
        )


class ResourcePolicySnapshotproperties(object):
    def __init__(self, request, module):
        self.module = module
        if request:
            self.request = request
        else:
            self.request = {}

    def to_request(self):
        return remove_nones_from_dict(
            {u'labels': self.request.get('labels'), u'storageLocations': self.request.get('storage_locations'), u'guestFlush': self.request.get('guest_flush')}
        )

    def from_response(self):
        return remove_nones_from_dict(
            {u'labels': self.request.get(u'labels'), u'storageLocations': self.request.get(u'storageLocations'), u'guestFlush': self.request.get(u'guestFlush')}
        )


if __name__ == '__main__':
    main()
