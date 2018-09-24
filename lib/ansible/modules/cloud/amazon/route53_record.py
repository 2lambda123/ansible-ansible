#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: route53_record
version_added: "2.8"
short_description: Creates,deletes DNS records in Amazon Route53 service.
description: Creates,deletes DNS records in Amazon Route53 service.
author: Shuang Wang (@ptux)

requirements:
  - botocore
  - boto3
  - python >= 2.6

options:
  state:
    description:
      - Specifies the state of the resource record.
    required: true
    choices: [ 'present', 'absent' ]
  hosted_zone_name:
    description:
      - The DNS zone to modify
    required: true
  hosted_zone_id:
    description:
      - The Hosted Zone ID of the DNS zone to modify
  record_set_name:
    description:
      - The full DNS record to create or delete
    required: true
  record_set_ttl:
    description:
      - The TTL(seconds) to give the new record
    type: int
    default: 3600
  record_set_type:
    description:
      - The type of DNS record to create
    required: true
    choices: [ 'A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA' ]
  record_set_value:
    description:
      - The new value when creating a DNS record.
  wait:
    description:
      - Wait until the changes have been replicated to all Amazon Route 53 DNS servers.
    type: bool
    default: 'no'
  wait_timeout:
    description:
      - How long to wait for the changes to be replicated, in seconds.
    default: 300

extends_documentation_fragment:
  - aws
  - ec2
'''

RETURN = '''
Name:
    description: record_set_name
    returned: always
    type: string
    sample: "sample.example.com"

ResourceRecords:
    description: record_set_name
    returned: always
    type: list
    sample: ['Value': 192.0.2.1, 'Value': 192.0.2.2]

TTL:
    description: record_set_name
    returned: always
    type: string
    sample: "300"

Type:
    description: record_set_name
    returned: always
    type: string
    sample: "A"
'''

EXAMPLES = '''
# Add new A record and wait until the changes replicated
- route53_record:
    state: present
    hosted_zone: example.com
    record_set_name: sample.example.com
    record_set_type: A
    record_set_ttl: 300
    record_set_value: 192.0.2.1
    wait: yes
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

#import time
from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils.ec2 import (
#    AWSRetry,
    boto3_conn,
    boto_exception,
    ec2_argument_spec
#    get_aws_connection_info,
#    snake_dict_to_camel_dict,
#    camel_dict_to_snake_dict
)


class AWSRoute53Record(object):
    def __init__(self, module=None):
        self._module = module
        self._connection = self._module.client('route53')
        self._check_mode = self._module.check_mode

    def process(self):

        if self._module.params['hosted_zone_id'] is not None:
            hosted_zone_id = self._module.params['hosted_zone_id']
            hosted_zone = self._connection.get_hosted_zone(Id=hosted_zone_id)
            spec_hosted_zone_name = self._module.params['hosted_zone_name']
            hosted_zone_name = hosted_zone['HostedZone']['Name']
            if not spec_hosted_zone_name.endswith('.'):
                spec_hosted_zone_name += "."
            if not spec_hosted_zone_name == hosted_zone_name:
                self._module.fail_json(msg="hosted_zone_id not matches hosted_zone_name")

        record_exists = self._record_exists()
        if self._module.params['state'] == 'present' and record_exists:
            results = dict(changed=False)
        if self._module.params['state'] == 'present' and not record_exists:
            if not self._module.check_mode:
                results = self._create_record()
            results = dict(changed=True)
        if self._module.params['state'] == 'absent' and record_exists:
            if not self._module.check_mode:
                results = self._delete_record()
            results = dict(changed=True)
        if self._module.params['state'] == 'absent' and not record_exists:
            results = dict(changed=False)
        return results

    def _record_exists(self):
        record_exists = False
        resource_record_sets = self._get_resource_record_sets()
        record_set_name = self._module.params['record_set_name']
        if not record_set_name.endswith('.'):
            record_set_name += "."
        record_set_type = self._module.params['record_set_type']
        record_set_ttl = self._module.params['record_set_ttl']
        record_set_value = self._module.params['record_set_value']
        list_record_set_value = [{'Value': value} for value in record_set_value]
        record_set_spec = {
            'Name': record_set_name,
            'ResourceRecords': list_record_set_value,
            'TTL': record_set_ttl,
            'Type': record_set_type
            }
        if record_set_spec in resource_record_sets:
            record_exists = True
        return record_exists

    def _get_hosted_zone_id(self, hosted_zone_name=None):
        """gets a zone id by zone name"""
        hosted_zone_id = None
        if hosted_zone_name is not None:
            try:
                hosted_zones = self._connection.list_hosted_zones().get('HostedZones', [])
                if not hosted_zone_name.endswith('.'):
                    hosted_zone_name += "."
                for dic in hosted_zones:
                    if dic.get('Name') == hosted_zone_name:
                        hosted_zone_id = dic.get('Id')
                if hosted_zone_id is None:
                    self._module.fail_json(msg="hosted zone name not exists: %s" % hosted_zone_name)
            except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
                self._module.fail_json_aws(e, msg="couldn't get hosted zone id by hosted_zone_name")
        else:
            self._module.fail_json(msg="hosted zone name is requied.")
        return hosted_zone_id

    def _get_resource_record_sets(self):
        # todo: hanlde IsTruncated true
        hosted_zone_name = self._module.params['hosted_zone_name']
        hosted_zone_id = self._get_hosted_zone_id(hosted_zone_name)
        resource_record_sets = self._connection.list_resource_record_sets(HostedZoneId=hosted_zone_id)['ResourceRecordSets']
        return resource_record_sets

    def _create_record(self):
        #      self._connection.change_resource_record_sets(**kwargs)
        pass

    def _delete_record(self):
        pass


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        hosted_zone_name=dict(required=True),
        hosted_zone_id=dict(required=False, default=None),
        record_set_name=dict(required=True),
        record_set_type=dict(choices=['A', 'CNAME', 'MX', 'AAAA', 'TXT', 'PTR', 'SRV', 'SPF', 'CAA', 'NS', 'SOA'], required=True),
        record_set_ttl=dict(required=False, type='int', default=3600),
        record_set_value=dict(required=False, type='list'),
        state=dict(choices=['present', 'absent'], required=True),
        wait=dict(required=False, type='bool', default=False),
        wait_timeout=dict(required=False, type='int', default=300)
    ))

    required_if = [('state', 'present', ['record_set_value']),
                   ('state', 'absent', ['record_set_value'])]

    ansible_aws_module = AnsibleAWSModule(
        argument_spec=argument_spec,
        required_if=required_if,
        supports_check_mode=True
    )
    aws_route53_record = AWSRoute53Record(module=ansible_aws_module)
    results = aws_route53_record.process()
    ansible_aws_module.exit_json(**results)


if __name__ == '__main__':
    main()
