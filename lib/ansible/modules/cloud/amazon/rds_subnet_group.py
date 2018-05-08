#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: rds_subnet_group
version_added: "1.5"
short_description: manage RDS database subnet groups
description:
     - Creates, modifies, and deletes RDS database subnet groups. This module has a dependency on python-boto >= 2.5.
options:
  state:
    description:
      - Specifies whether the subnet should be present or absent.
    required: true
    default: present
    choices: [ 'present' , 'absent' ]
  name:
    description:
      - Database subnet group identifier.
    required: true
  description:
    description:
      - Database subnet group description. Only set when a new group is added.
  subnets:
    description:
      - List of subnet IDs that make up the database subnet group.
author: "Scott Anderson (@tastychutney)"
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Add or change a subnet group
- rds_subnet_group:
    state: present
    name: norwegian-blue
    description: My Fancy Ex Parrot Subnet Group
    subnets:
      - subnet-aaaaaaaa
      - subnet-bbbbbbbb

# Remove a subnet group
- rds_subnet_group:
    state: absent
    name: norwegian-blue
'''

RETURN = '''
subnet_group:
    description: Dictionary of DB subnet group values
    returned: I(state=present)
    type: complex
    contains:
        name:
            description: The name of the DB subnet group
            returned: I(state=present)
            type: string
        description:
            description: The description of the DB subnet group
            returned: I(state=present)
            type: string
        vpc_id:
            description: The VpcId of the DB subnet group
            returned: I(state=present)
            type: string
        subnet_ids:
            description: Contains a list of Subnet IDs
            returned: I(state=present)
            type: array
        status:
            description: The status of the DB subnet group
            returned: I(state=present)
            type: string
'''

try:
    import boto.rds
    from boto.exception import BotoServerError
    HAS_BOTO = True
except ImportError:
    HAS_BOTO = False

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO, connect_to_aws, ec2_argument_spec, get_aws_connection_info


def create_partial_subnet_group_info(name, desc, subnets):
    return dict(
        name=name,
        description=desc,
        subnet_ids=subnets
    )


def get_subnet_group_info(subnet_group):
    return dict(
        name=subnet_group.name,
        description=subnet_group.description,
        vpc_id=subnet_group.vpc_id,
        subnet_ids=subnet_group.subnet_ids,
        status=subnet_group.status
    )


def has_different_value(actual, expected):
    # Sort the subnet groups before we compare them
    actual['subnet_ids'].sort()
    expected['subnet_ids'].sort()
    fields = ['name', 'description', 'subnet_ids']
    return extract(actual, fields) != extract(expected, fields)


def extract(dic, fields):
    return {f: dic[f] for f in fields}


def create_result(changed, subnet_group=None):
    if subnet_group is None:
        return dict(
            changed=changed
        )
    else:
        return dict(
            changed=changed,
            subnet_group=subnet_group
        )


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        state=dict(required=True, choices=['present', 'absent']),
        name=dict(required=True),
        description=dict(required=False),
        subnets=dict(required=False, type='list'),
    )
    )
    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    if not HAS_BOTO:
        module.fail_json(msg='boto required for this module')

    state = module.params.get('state')
    group_name = module.params.get('name').lower()
    group_description = module.params.get('description')
    group_subnets = module.params.get('subnets') or {}

    if state == 'present':
        for required in ['name', 'description', 'subnets']:
            if not module.params.get(required):
                module.fail_json(msg=str("Parameter %s required for state='present'" % required))
    else:
        for not_allowed in ['description', 'subnets']:
            if module.params.get(not_allowed):
                module.fail_json(msg=str("Parameter %s not allowed for state='absent'" % not_allowed))

    # Retrieve any AWS settings from the environment.
    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module)

    if not region:
        module.fail_json(msg=str("Either region or AWS_REGION or EC2_REGION environment variable or boto config aws_region or ec2_region must be set."))

    try:
        conn = connect_to_aws(boto.rds, region, **aws_connect_kwargs)
    except BotoServerError as e:
        module.fail_json(msg=e.error_message)

    try:
        check_mode = module.check_mode
        exists = False
        result = create_result(False)

        try:
            matching_groups = conn.get_all_db_subnet_groups(group_name, max_records=100)
            exists = len(matching_groups) > 0
        except BotoServerError as e:
            if e.error_code != 'DBSubnetGroupNotFoundFault':
                module.fail_json(msg=e.error_message)

        if state == 'absent':
            if exists:
                # delete
                if not check_mode:
                    conn.delete_db_subnet_group(group_name)
                result = create_result(True)
        else:
            expected_group = create_partial_subnet_group_info(group_name, group_description, group_subnets)
            if exists:
                # modify or do nothing
                target_group = get_subnet_group_info(matching_groups[0])
                if has_different_value(target_group, expected_group):
                    changed_group = None
                    if check_mode:
                        changed_group = target_group.copy()
                        changed_group.update(expected_group)
                    else:
                        changed_group = conn.modify_db_subnet_group(group_name, description=group_description, subnet_ids=group_subnets)
                        changed_group = get_subnet_group_info(changed_group)
                    result = create_result(True, changed_group)
                else:
                    result = create_result(False, target_group)
            else:
                # create
                if check_mode:
                    result = create_result(True, expected_group)
                else:
                    new_group = conn.create_db_subnet_group(group_name, desc=group_description, subnet_ids=group_subnets)
                    result = create_result(True, get_subnet_group_info(new_group))
    except BotoServerError as e:
        module.fail_json(msg=e.error_message)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
