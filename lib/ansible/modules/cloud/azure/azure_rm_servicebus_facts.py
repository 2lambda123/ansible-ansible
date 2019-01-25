#!/usr/bin/python
#
# Copyright (c) 2018 Yuwei Zhou, <yuwzho@microsoft.com>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: azure_rm_servicebus_facts

version_added: "2.8"

short_description: Get servicebus facts.

description:
    - Get facts for a specific servicebus or all servicebus in a resource group or subscription.

options:
    name:
        description:
            - Limit results to a specific servicebus.
    resource_group:
        description:
            - Limit results in a specific resource group.
    tags:
        description:
            - Limit results by providing a list of tags. Format tags as 'key' or 'key:value'.
    namespace:
        description:
            - Servicebus namespace name.
            - A namespace is a scoping container for all messaging components.
            - Multiple queues and topics can reside within a single namespace, and namespaces often serve as application containers.
            - Required when C(type) is not C(namespace).

extends_documentation_fragment:
    - azure

author:
    - "Yuwei Zhou (@yuwzho)"

'''

EXAMPLES = '''
    - name: Get facts for one servicebus
      azure_rm_servicebus_facts:
        name: Testing
        resource_group: foo

    - name: Get facts for all servicebuss
      azure_rm_servicebus_facts:
        resource_group: foo

    - name: Get facts by tags
      azure_rm_servicebus_facts:
        tags:
          - testing
          - foo:bar
'''
RETURN = '''

id:
    description:
      -  Resource Id
name:
    description:
      -  Resource name
location:
    description:
      -  The Geo-location where the resource lives 
namespace:
    description:
      - Namespace name of the queue or topic, subscription.
topic:
    description:
      - Topic name of a subscription.
tags:
    description:
      -  Resource tags 
sku:
    description:
      -  Porperties of Sku 
provisioning_state:
    description:
      -  Provisioning state of the namespace.
service_bus_endpoint:
    description:
      -  Endpoint you can use to perform Service Bus operations.
metric_id:
    description:
      -  Identifier for Azure Insights metrics
type:
    description:
      - Resource type
      - Namespace is a scoping container for all messaging components.
      - Queue enables you to store messages until the receiving application is available to receive and process them.
      - Topic and subscriptions enable 1:n relationships between publishers and subscribers.
    sample: "Microsoft.ServiceBus/Namespaces/Topics"
size_in_bytes:
    description:
      - Size of the topic, in bytes.
created_at:
    description:
      - Exact time the message was created.
    sample: "2019-01-25 02:46:55.543953+00:00"
updated_at:
    description:
      - The exact time the message was updated.
    sample: "2019-01-25 02:46:55.543953+00:00"
accessed_at:
    description:
      - Last time the message was sent, or a request was received, for this topic.
    sample: "2019-01-25 02:46:55.543953+00:00"
subscription_count:
    description:
      - Number of subscriptions.
count_details:
    description:
        - Message count deatils.
    contains:
        active_message_count:
            description:
               - Number of active messages in the queue, topic, or subscription.
        dead_letter_message_count:
            description:
               - Number of messages that are dead lettered.
        scheduled_message_count:
            description:
               - Number of scheduled messages.
        transfer_message_count:
            description:
               - Number of messages transferred to another queue, topic, or subscription.
        transfer_dead_letter_message_count:
            description:
               - Number of messages transferred into dead letters.
support_ordering:
    description:
      - Value that indicates whether the topic supports ordering.
status:
    description:
      - The status of a messaging entity.
requires_session:
    description:
      - A value that indicates whether the  queue or topic supports the concept of sessions.
requires_duplicate_detection:
    description:
      - A value indicating if this queue or topic requires duplicate detection.
max_size_in_mb:
    description:
      - Maximum size of the queue or topic in megabytes, which is the size of the memory allocated for the topic.
max_delivery_count:
    description:
      - The maximum delivery count.
      - A message is automatically deadlettered after this number of deliveries.
lock_duration_in_seconds:
    description:
      - ISO 8601 timespan duration of a peek-lock.
      - The amount of time that the message is locked for other receivers.
      - The maximum value for LockDuration is 5 minutes.
forward_to:
    description:
      - Queue or topic name to forward the messages
forward_dead_lettered_messages_to:
    description:
      - Queue or topic name to forward the Dead Letter message
enable_partitioning:
    description:
      - Value that indicates whether the queue or topic to be partitioned across multiple message brokers is enabled.
enable_express:
    description:
      - Value that indicates whether Express Entities are enabled.
      - An express topic holds a message in memory temporarily before writing it to persistent storage.
enable_batched_operations:
    description:
      - Value that indicates whether server-side batched operations are enabled.
duplicate_detection_time_in_seconds:
    description:
      - ISO 8601 timeSpan structure that defines the duration of the duplicate detection history.
default_message_time_to_live_seconds:
    description:
      - ISO 8061 Default message timespan to live value.
      - This is the duration after which the message expires, starting from when the message is sent to Service Bus.
      - This is the default value used when TimeToLive is not set on a message itself.
dead_lettering_on_message_expiration:
    description:
      - A value that indicates whether this  queue or topic has dead letter support when a message expires.
dead_lettering_on_filter_evaluation_exceptions:
    description:
      - Value that indicates whether a subscription has dead letter support on filter evaluation exceptions.
auto_delete_on_idle_in_seconds:
    description:
      - ISO 8061 timeSpan idle interval after which the  queue or topic is automatically deleted.
      - The minimum duration is 5 minutes.
size_in_bytes:
    description:
      - The size of the queue or topic, in bytes.
message_count:
    description:
      - Number of messages.

'''

try:
    from msrestazure.azure_exceptions import CloudError
except Exception:
    # This is handled in azure_rm_common
    pass

from ansible.module_utils.azure_rm_common import AzureRMModuleBase, azure_id_to_dict
from ansible.module_utils.common.dict_transformations import _camel_to_snake
from ansible.module_utils._text import to_native
from datetime import datetime, timedelta

duration_spec_map = dict(
    default_message_time_to_live='default_message_time_to_live_seconds',
    duplicate_detection_history_time_window='duplicate_detection_time_in_seconds',
    auto_delete_on_idle='auto_delete_on_idle_in_seconds',
    lock_duration='lock_duration_in_seconds'
)


def is_valid_timedelta(value):
    if value == timedelta(10675199, 10085, 477581):
        return None
    return value


class AzureRMServiceBusFacts(AzureRMModuleBase):

    def __init__(self):

        self.module_arg_spec = dict(
            name=dict(type='str'),
            resource_group=dict(type='str'),
            tags=dict(type='list'),
            type=dict(type='str',required=True, choices=['namespace', 'topic', 'queue', 'subscription']),
            namespace=dict(type='str'),
            topic=dict(type='str'),
            show_sas_policies=dict(type='bool')
        )

        required_if = [
            ('type', 'subscription', ['topic', 'resource_group', 'namespace']),
            ('type', 'topic', ['resource_group', 'namespace']),
            ('type', 'queue', ['resource_group', 'namespace'])
        ]

        self.results = dict(
            changed=False,
            servicebuses=[]
        )

        self.name = None
        self.resource_group = None
        self.tags = None
        self.type = None
        self.namespace = None
        self.topic = None
        self.show_sas_policies = None

        super(AzureRMServiceBusFacts, self).__init__(self.module_arg_spec,
                                                     supports_tags=False,
                                                     required_if=required_if,
                                                     facts_module=True)

    def exec_module(self, **kwargs):

        for key in self.module_arg_spec:
            setattr(self, key, kwargs[key])

        response = []
        if self.name:
            response = self.get_item()
        elif self.resource_group:
            response = self.list_items()
        else:
            response = self.list_all_items()

        self.results['servicebuses'] = [self.instance_to_dict(x) for x in response]
        return self.results

    def instance_to_dict(self, instance):
        result = dict()
        instance_type = getattr(self.servicebus_models, 'SB{0}'.format(str.capitalize(self.type)))
        attribute_map = instance_type._attribute_map
        for attribute in attribute_map.keys():
            value = getattr(instance, attribute)
            if attribute_map[attribute]['type'] == 'duration':
                if is_valid_timedelta(value):
                    key = duration_spec_map.get(attribute) or attribute
                    result[key] = int(value.total_seconds())
            elif attribute == 'status':
                result['status'] = _camel_to_snake(value)
            elif isinstance(value, self.servicebus_models.MessageCountDetails):
                result[attribute] = value.as_dict()
            elif isinstance(value, str):
                result[attribute] = to_native(value)
            elif attribute == 'max_size_in_megabytes':
                result['max_size_in_mb'] = value
            else:
                result[attribute] = str(value)
        if self.show_sas_policies and self.type != 'subscription':
            policies = self.get_auth_rules()
            for name in policies.keys():
                policies[name] = self.get_sas_key(name)
            result['sas_policies'] = policies
        if self.namespace:
            result['namespace'] = self.namespace
        if self.topic:
            result['topic'] = self.topic
        return  result

    def _get_client(self):
        return getattr(self.servicebus_client, '{0}s'.format(self.type))

    def get_item(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                item = client.get(self.resource_group, self.name)
                return [item] if self.has_tags(item.tags, self.tags) else []
            elif self.type == 'subscription':
                return [client.get(self.resource_group, self.namespace, self.topic, self.name)]
            else:
                return [client.get(self.resource_group, self.namespace, self.name)]
        except CloudError:
            pass
        return []

    def list_items(self):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                response = client.list_by_resource_group(self.resource_group)
                return [x for x in response if self.has_tags(x.tags, self.tags)]
            elif self.type == 'subscription':
                return client.list_by_topic(self.resource_group, self.namespace, self.topic)
            else:
                return client.list_by_namespace(self.resource_group, self.namespace)
        except CloudError as exc:
            self.fail("Failed to list items - {0}".format(str(exc)))
        return []

    def list_all_items(self):
        self.log("List all items in subscription")
        try:
            if self.type != 'namespace':
                return []
            response = self.servicebus_client.namespaces.list()
            return [x for x in response if self.has_tags(x.tags, self.tags)]
        except CloudError as exc:
            self.fail("Failed to list all items - {0}".format(str(exc)))
        return []

    def get_auth_rules(self):
        result = dict()
        try:
            client = self._get_client()
            if self.type == 'namespace':
                rules = client.list_authorization_rules(self.resource_group, self.name)
            else:
                rules = client.list_authorization_rules(self.resource_group, self.namespace, self.name)
            while True:
                rule = rules.next()
                result[rule.name] = self.policy_to_dict(rule)
        except StopIteration:
            pass
        except Exception as exc:
            self.fail('Error when getting SAS policies for {0} {1}: {2}'.format(self.type, self.name, exc.message or str(exc)))
        return result

    def get_sas_key(self, name):
        try:
            client = self._get_client()
            if self.type == 'namespace':
                return client.list_keys(self.resource_group, self.name, name).as_dict()
            else:
                return client.list_keys(self.resource_group, self.namespace, self.name, name).as_dict()
        except Exception as exc:
            self.fail('Error when getting SAS policy {0}\'s key - {1}'.format(name, exc.message or str(exc)))
        return None

    def policy_to_dict(self, rule):
        result = rule.as_dict()
        rights = result['rights']
        if 'Manage' in rights:
            result['rights'] = 'manage'
        elif 'Listen' in rights and 'Send' in rights:
            result['rights'] = 'listen_send'
        else:
            result['rights'] = rights[0].lower()
        return result


def main():
    AzureRMServiceBusFacts()


if __name__ == '__main__':
    main()
