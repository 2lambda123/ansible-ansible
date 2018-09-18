#!/usr/bin/python

# Copyright: (c) Ansible Project
# Copyright: (c) 2018, Shuang Wang <ooocamel@icloud.com>

# This code refactors the module route53.py of Ansible in order to support boto3.
# Name this module [route53_record] for the consistency with other route53_xxx modules.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'metadata_version': '1.1'}

DOCUMENTATION = '''
---
module: route53_record
version_added: "2.8"
author: Shuang Wang (@ptux)
short_description: add or delete entries in Amazons Route53 DNS service
requirements:
  - botocore
  - boto3
  - python >= 2.7
extends_documentation_fragment:
  - aws
  - ec2
'''

EXAMPLES = '''
'''

RETURN = '''
'''

try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from ansible.module_utils.aws.core import AnsibleAWSModule
from ansible.module_utils._text import to_native
from ansible.module_utils.ec2 import (
    AWSRetry,
    boto3_conn,
    ec2_argument_spec,
    get_aws_connection_info,
    camel_dict_to_snake_dict,
    boto3_tag_list_to_ansible_dict,
    ansible_dict_to_boto3_filter_list,
    ansible_dict_to_boto3_tag_list,
    compare_aws_tags
)


class AWSRoute53Record(object):
    def __init__(self, module=None, results=None):
        self._module = module
        self._results = results
        self._connection = self._module.client('ec2')
        self._check_mode = self._module.check_mode
        self.warnings = []

    def _read_zone(self):
        pass

    def _create_record(self):
        pass

    def _read_record(self):
        pass

    def _update_record(self):
        pass

    def _delete_record(self):
        pass

    def ensure_present(self):
        pass

    def ensure_absent(self):
        pass

    def process(self):
        pass


def main():
    argument_spec = ec2_argument_spec()

    argument_spec.update(dict(
    ))

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )
    results = dict(changed=False)

record_controller = AWSRoute53Record(module=module, results=results)
record_controller.process()

module.exit_json(**results)

if __name__ == '__main__':
    main()
