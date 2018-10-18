#!/usr/bin/python
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: code_pipeline
short_description: Create or delete AWS CodePipeline
notes:
    - for details of the parameters and returns see U(http://boto3.readthedocs.io/en/latest/reference/services/codepipeline.html)
description:
    - Create or delete a CodePipeline on AWS.
version_added: "2.6"
author:
    - Stefan Horning (@stefanhorning) <horning@mediapeers.com>
requirements: [ json, botocore, boto3 ]
options:
    name:
        description:
            - Name of the pipeline
        required: true
    role_arn:
        description:
            - ARN of the IAM role to use when executing the pipeline
        required: true
    artifact_store:
        description:
            - Location information where articacts are stored (on S3). Dictionary with fields type and location.
        required: true
    stages:
        description:
            - List of stages to perfoem in the CodePipeline. List of dictionaries
        required: true
    version:
        description:
            - Version number of the pipeline. This number is automatically incremented when a pipeline is updated.
        required: false
    state:
        description:
            - Create or remove code pipeline
        default: 'present'
        choices: ['present', 'absent']
extends_documentation_fragment:
    - aws
    - ec2
'''

EXAMPLES = '''
# Note: These examples do not set authentication details, see the AWS Guide for details.

# Example for creating a pipeline for continouos deploy of Github code to an ECS cluster (container)
- code_pipeline:
    name: my_deploy_pipeline
    role_arn: arn:aws:iam::123456:role/AWS-CodePipeline-Service
    artifact_store:
      type: S3
      locatation: my_s3_codepipline_bucket
    stages:
      - name: Get_source
        actions:
          -
            name: Git_pull
            actionTypeId:
              category: Source
              owner: ThirdParty
              provider: GitHub
              version: '1'
            outputArtifacts:
              - { name: my-app-source }
            configuration:
              Owner: mediapeers
              Repo: my_gh_repo
              PollForSourceChanges: 'true'
              Branch: master
              # Generate token like this:
              # https://docs.aws.amazon.com/codepipeline/latest/userguide/GitHub-rotate-personal-token-CLI.html
              # GH Link: https://github.com/settings/tokens
              OAuthToken: 'abc123def456'
            runOrder: 1
      - name: Build
        actions:
          -
            name: CodeBuild
            actionTypeId:
              category: Build
              owner: AWS
              provider: CodeBuild
              version: '1'
            inputArtifacts:
              - { name: my-app-source }
            outputArtifacts:
              - { name: my-app-build }
            configuration:
              # A project with that name needs to be setup on AWS CodeBuild already (use code_build module).
              ProjectName: codebuild-project-name
            runOrder: 1
      - name: ECS_deploy
        actions:
          -
            name: ECS_deploy
            actionTypeId:
              category: Deploy
              owner: AWS
              provider: ECS
              version: '1'
            inputArtifacts:
              - { name: vod-api-app-build }
            configuration:
              # an ECS cluster with that name needs to be setup on AWS ECS already (use ecs_cluster and ecs_service module)
              ClusterName: ecs-cluster-name
              ServiceName: ecs-cluster-service-name
              FileName: imagedefinitions.json
    region: us-east-1
    state: present
'''

RETURN = '''
pipeline:
  description: Returns the dictionary desribing the code pipeline configuration.
  returned: success
  type: complex
  contains:
    name:
      description: Name of the CodePipeline
      returned: always
      type: string
      sample: my_deploy_pipeline
    role_arn:
      description: ARN of the IAM role attached to the code pipeline
      returned: always
      type: string
      sample: arn:aws:iam::123123123:role/codepipeline-service-role
    artifact_store:
      description: Information about where the build artifacts are stored
      returned: always
      type: complex
      contains:
        type:
          desrciption: The type of the artifacts store, such as S3
          returned: always
          type: string
          sample: S3
        location:
          description: The location of the artifacts storage (s3 bucket name)
          returned: always
          type: string
          sample: my_s3_codepipline_bucket
        encryption_key:
          description: The encryption key used to encrypt the artifacts store, such as an AWS KMS key.
          returned: when configured
          type: string
    stages:
      description: List of stages configured for this pipeline
      returned: always
      type: list
    version:
      description: THe version number of the pipeline. This number is auto incremented when pipeline params are changed.
      returned: always
      type: int
'''

import traceback
from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.ec2 import HAS_BOTO3, camel_dict_to_snake_dict, boto3_conn, ec2_argument_spec, get_aws_connection_info

try:
    import botocore
except ImportError:
    pass  # will be detected by imported HAS_BOTO3


def create_pipeline(client, name, role_arn, artifact_store, stages, version, module):
    pipeline_dict = {'name': name, 'roleArn': role_arn, 'artifactStore': artifact_store, 'stages': stages}
    if version:
        pipeline_dict['version'] = version
    try:
        resp = client.create_pipeline(pipeline=pipeline_dict)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable create pipeline {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to create pipeline {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def update_pipeline(client, pipeline_dict, module):
    try:
        resp = client.update_pipeline(pipeline=pipeline_dict)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable update pipeline {0}: {1}".format(pipeline_dict['name'], to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to update pipeline {0}: {1}".format(pipeline_dict['name'], to_native(e)),
                         exception=traceback.format_exc())


def delete_pipeline(client, name, module):
    try:
        resp = client.delete_pipeline(name=name)
        return resp
    except botocore.exceptions.ClientError as e:
        module.fail_json(msg="Unable delete pipeline {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc(), **camel_dict_to_snake_dict(e.response))
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Unable to delete pipeline {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def describe_pipeline(client, name, version, module):
    pipeline = {}
    try:
        if isinstance(version, int) is int:
            pipeline = client.get_pipeline(name=name, version=version)
            return pipeline
        else:
            pipeline = client.get_pipeline(name=name)
            return pipeline
    except botocore.exceptions.ClientError as e:
        return pipeline
    except botocore.exceptions.BotoCoreError as e:
        module.fail_json(msg="Error when calling client.get_pipeline {0}: {1}".format(name, to_native(e)),
                         exception=traceback.format_exc())


def main():
    argument_spec = ec2_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True, type='str'),
        role_arn=dict(required=True, type='str'),
        artifact_store=dict(required=True, type='dict'),
        stages=dict(required=True, type='list'),
        version=dict(required=False, type='int'),
        state=dict(choices=['present', 'absent'], default='present')
    ))

    module = AnsibleModule(argument_spec=argument_spec)

    if not HAS_BOTO3:
        module.fail_json(msg='boto3 is required.')

    region, ec2_url, aws_connect_kwargs = get_aws_connection_info(module, boto3=True)
    client_conn = boto3_conn(module, conn_type='client', resource='codepipeline', region=region, endpoint=ec2_url, **aws_connect_kwargs)

    state = module.params.get('state')
    changed = False

    # Determine if the CodePipeline exists
    found_code_pipeline = describe_pipeline(client=client_conn, name=module.params['name'], version=module.params['version'], module=module)
    pipeline_result = {}

    if state == 'present':
        if 'pipeline' in found_code_pipeline:
            pipeline_dict = found_code_pipeline['pipeline']
            # Update dictionary with provided module params:
            pipeline_dict['roleArn'] = module.params['role_arn']
            pipeline_dict['artifactStore'] = module.params['artifact_store']
            pipeline_dict['stages'] = module.params['stages']
            if isinstance(module.params['version'], int):
                pipeline_dict['version'] = module.params['version']

            pipeline_result = update_pipeline(client=client_conn, pipeline_dict=pipeline_dict, module=module)
            changed = True
        else:
            pipeline_result = create_pipeline(
                client=client_conn,
                name=module.params['name'],
                role_arn=module.params['role_arn'],
                artifact_store=module.params['artifact_store'],
                stages=module.params['stages'],
                version=module.params['version'],
                module=module)
            changed = True
    elif state == 'absent':
        if found_code_pipeline:
            pipeline_result = delete_pipeline(client=client_conn, name=module.params['name'], module=module)
            changed = True

    module.exit_json(changed=changed, **camel_dict_to_snake_dict(pipeline_result))

if __name__ == '__main__':
    main()
