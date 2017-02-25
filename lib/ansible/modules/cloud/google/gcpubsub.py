#!/usr/bin/python
# Copyright 2016 Google Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'status': ['preview'],
                    'supported_by': 'community',
                    'version': '1.0'}

DOCUMENTATION = '''
---
module: gcpubsub
version_added: "2.3"
short_description: Create and Delete Topics/Subscriptions, Publish and pull messages on PubSub.
description:
    - Create and Delete Topics/Subscriptions, Publish and pull messages on PubSub.
      See U(https://cloud.google.com/pubsub/docs) for an overview.
requirements:
  - "python >= 2.6"
  - "google-auth >= 0.5.0"
  - "google-cloud-pubsub >= 0.22.0"
notes:
  - Subscription pull happens before publish.  You cannot publish and pull in the same task.
author:
  - "Tom Melendez (@supertom) <tom@supertom.com>"
options:
  topic:
    description:
       - GCP pubsub topic name.  Only the name, not the full path, is required.
    required: True
  subscription:
    description:
       - Dictionary containing a subscripton name associated with a topic (required), along with optional ack_deadline, push_endpoint and pull. For pulling from a subscription, message_ack (bool), max_messages (int) and return_immediate are available as subfields.  See subfields name, push_endpoint and ack_deadline for more information.
    required: False
  name:
    description: Subfield of subscription. Required if subscription is specified. See examples.
    required: False
  ack_deadline:
    description: Subfield of subscription. Not required. Default deadline for subscriptions to ACK the message before it is resent. See examples.
    required: False
  pull:
    description: Subfield of subscription. Not required. If specified, messages will be retrieved from topic via the provided subscription name. max_messages (int; default None; max number of messages to pull), message_ack (bool; default False; acknowledge the message) and return_immediately (bool; default True, don't wait for messages to appear). If the messages are acknowledged, changed is set to True, otherwise, changed is False.
  push_endpoint:
    description: Subfield of subscription.  Not required.  If specified, message will be sent to an endpoint. See U(https://cloud.google.com/pubsub/docs/advanced#push_endpoints) for more information.
    required: False
  publish:
    description: List of dictionaries describing messages and attributes to be published.  Dictionary is in message(str):attributes(dict) format. Only message is required.
    required: False
  state:
    description: State of the topic or queue (absent, present). Applies to the most granular resource. Remove the most granular resource.  If subcription is specified we remove it.  If only topic is specified, that is what is removed. Note that a topic can be removed without first removing the subscription.
    required: False
    default: "present"
'''
EXAMPLES = '''
# Create a topic and publish a message to it
# (Message will be pushed; there is no check to see if the message was pushed before
# Topics:
## Create Topic
gcpubsub:
  topic: ansible-topic-example
  state: present

## Delete Topic
### Subscriptions associated with topic are not deleted.
gcpubsub:
  topic: ansible-topic-example
  state: absent

## Messages: publish multiple messages, with attributes (key:value available with the message)
### setting absent will keep the messages from being sent
gcpubsub:
  topic: "{{ topic_name }}"
  state: present
  publish:
    - message: "this is message 1"
      attributes:
        mykey1: myvalue
        mykey2: myvalu2
        mykey3: myvalue3
    - message: "this is message 2"
      attributes:
        server: prod
        sla: "99.9999"
        owner: fred

# Subscriptions
## Create Subscription (pull)
gcpubsub:
  topic: ansible-topic-example
  subscription:
  - name: mysub
  state: present

## Create Subscription with ack_deadline and push endpoint
### pull is default, ack_deadline is not required
gcpubsub:
  topic: ansible-topic-example
  subscription:
  - name: mysub
    ack_deadline: "60"
    push_endpoint: http://pushendpoint.example.com
  state: present

## Subscription change from push to pull
### setting push_endpoint to "None" converts subscription to pull.
gcpubsub:
  topic: ansible-topic-example
  subscription:
    name: mysub
    push_endpoint: "None"

## Delete subscription
### Topic will not be deleted
gcpubsub:
  topic: ansible-topic-example
  subscription:
  - name: mysub
  state: absent

## Pull messages from subscription
### only pull keyword is required.
gcpubsub:
  topic: ansible-topic-example
  subscription:
    name: ansible-topic-example-sub
    pull:
      message_ack: yes
      max_messages: "100"
'''

RETURN = '''
publish:
    description: List of dictionaries describing messages and attributes to be published.  Dictionary is in message(str):attributes(dict) format. Only message is required.
    returned: Only when specified
    type: list of dictionary
    sample: "publish: ['message': 'my message', attributes: {'key1': 'value1'}]"

pulled_messages:
    description: list of dictionaries containing message info.  Fields are ack_id, attributes, data, message_id.
    returned: Only when subscription.pull is specified
    type: list of dictionary
    sample: [{ "ack_id": "XkASTCcYREl...","attributes": {"key1": "val1",...}, "data": "this is message 1", "message_id": "49107464153705"},..]

state:
    description: The state of the topic or subscription. Value will be either 'absent' or 'present'.
    returned: Always
    type: str
    sample: "present"

subscription:
    description: Name of subscription.
    returned: When subscription fields are specified
    type: str
    sample: "mysubscription"

topic:
    description: Name of topic.
    returned: Always
    type: str
    sample: "mytopic"
'''
CLOUD_CLIENT = 'google-cloud-pubsub'
CLOUD_CLIENT_MINIMUM_VERSION = '0.22.0'
CLOUD_CLIENT_USER_AGENT = 'ansible-pubsub-0.1'

try:
    from ast import literal_eval
    HAS_PYTHON26 = True
except ImportError:
    HAS_PYTHON26 = False

try:
    from google.cloud import pubsub
    HAS_GOOGLE_CLOUD_PUBSUB = True
except ImportError as e:
    HAS_GOOGLE_CLOUD_PUBSUB = False


def publish_messages(message_list, topic):
    with topic.batch() as batch:
        for message in message_list:
            msg = message['message']
            attrs = {}
            if 'attributes' in message:
                attrs = message['attributes']
            batch.publish(bytes(msg), **attrs)
    return True

def pull_messages(pull_params, sub):
    """
    :rtype: tuple (output, changed)
    """
    changed = False
    max_messages=pull_params.get('max_messages', None)
    message_ack = pull_params.get('message_ack', 'no')
    return_immediately = pull_params.get('return_immediately', False)

    output= []
    pulled = sub.pull(return_immediately=return_immediately,
                    max_messages=max_messages)

    for ack_id, msg in pulled:
        msg_dict = {'message_id': msg.message_id,
                    'attributes': msg.attributes,
                    'data': msg.data,
                    'ack_id': ack_id }
        output.append(msg_dict)

    if message_ack:
        ack_ids = [m['ack_id'] for m in output]
        if ack_ids:
            sub.acknowledge(ack_ids)
            changed = True
    return (output, changed)


def main():

    module = AnsibleModule(argument_spec=dict(
        topic=dict(required=True),
        state=dict(choices=['absent', 'present'], default='present'),
        publish=dict(type='list', default=None),
        subscription=dict(type='dict', default=None),
        service_account_email=dict(),
        credentials_file=dict(),
        project_id=dict(), ),)

    if not HAS_PYTHON26:
        module.fail_json(
            msg="GCE module requires python's 'ast' module, python v2.6+")

    if not HAS_GOOGLE_CLOUD_PUBSUB:
        module.fail_json(msg="Please install google-cloud-pubsub library.")

    if not check_min_pkg_version(CLOUD_CLIENT, CLOUD_CLIENT_MINIMUM_VERSION):
        module.fail_json(msg="Please install %s client version %s" % (CLOUD_CLIENT, CLOUD_CLIENT_MINIMUM_VERSION))

    mod_params = {}
    mod_params['publish'] = module.params.get('publish')
    mod_params['state'] = module.params.get('state')
    mod_params['topic'] = module.params.get('topic')
    mod_params['subscription'] = module.params.get('subscription')

    creds, params = get_google_cloud_credentials(module)
    pubsub_client = pubsub.Client(project=params['project_id'], credentials=creds, use_gax=False)
    pubsub_client.user_agent = CLOUD_CLIENT_USER_AGENT

    changed = False
    json_output = {}

    t = None
    if mod_params['topic']:
        t = pubsub_client.topic(mod_params['topic'])
    s = None
    if mod_params['subscription']:
        # Note: default ack deadline cannot be changed without deleting/recreating subscription
        s = t.subscription(mod_params['subscription']['name'],
                           ack_deadline=mod_params['subscription'].get('ack_deadline', None),
                           push_endpoint=mod_params['subscription'].get('push_endpoint', None))

    if mod_params['state'] ==  'absent':
        # Remove the most granular resource.  If subcription is specified
        # we remove it.  If only topic is specified, that is what is removed.
        # Note that a topic can be removed without first removing the subscription.
        # TODO(supertom): Enhancement: Provide an option to only delete a topic
        # if there are no subscriptions associated with it (which the API does not support).
        if s is not None:
            if s.exists():
                s.delete()
                changed = True
        else:
            if t.exists():
                t.delete()
                changed = True
    elif mod_params['state'] ==  'present':
        if not t.exists():
            t.create()
            changed = True
        if s:
            if not s.exists():
                s.create()
                s.reload()
                changed = True
            else:
                # Subscription operations
                # TODO(supertom): if more 'update' operations arise, turn this into a function.
                s.reload()
                push_endpoint=mod_params['subscription'].get('push_endpoint', None)
                if push_endpoint is not None:
                    if push_endpoint != s.push_endpoint:
                        if push_endpoint == 'None':
                            push_endpoint = None
                        s.modify_push_configuration(push_endpoint=push_endpoint)
                        s.reload()
                        changed = push_endpoint == s.push_endpoint

                if 'pull' in mod_params['subscription']:
                    if s.push_endpoint is not None:
                        module.fail_json(msg="Cannot pull messages, push_endpoint is configured.")
                    (json_output['pulled_messages'], changed) = pull_messages(
                        mod_params['subscription']['pull'], s)

        # publish messages to the topic
        if mod_params['publish'] and len(mod_params['publish']) > 0:
            changed = publish_messages(mod_params['publish'], t)


    json_output['changed'] = changed
    json_output.update(mod_params)
    module.exit_json(**json_output)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.gcp import *
if __name__ == '__main__':
    main()
