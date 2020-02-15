# (c) 2020, Julien Huon <@julienhuon> Institut National de l'Audiovisuel
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function

__metaclass__ = type

import copy

from ansible.module_utils.k8s.common import KubernetesAnsibleModule, AUTH_ARG_SPEC


class KubernetesAnsibleRollbackModule(KubernetesAnsibleModule):

    def __init__(self, *args, **kwargs):
        KubernetesAnsibleModule.__init__(self, *args,
                                         supports_check_mode=True,
                                         **kwargs)
        self.kind = self.params['kind']
        self.api_version = self.params['api_version']
        self.name = self.params['name']
        self.namespace = self.params['namespace']
        self.managed_resource = {}

        if self.kind == "DaemonSet":
            self.managed_resource['kind'] = "ControllerRevision"
            self.managed_resource['api_version'] = "apps/v1"
        elif self.kind == "Deployment":
            self.managed_resource['kind'] = "ReplicaSet"
            self.managed_resource['api_version'] = "apps/v1"
        else:
            self.fail(msg="Cannot perform rollback on resource of kind {0}"
                      .format(self.kind))

    def execute_module(self):
        results = []
        self.client = self.get_api_client()

        resources = self.kubernetes_facts(self.kind,
                                          self.api_version,
                                          self.name,
                                          self.namespace,
                                          self.params['label_selectors'],
                                          self.params['field_selectors'])

        for resource in resources['resources']:
            result = self.perform_action(resource)
            results.append(result)

        if len(results) == 1:
            self.exit_json(**results[0])

        self.exit_json(**{
            'changed': True,
            'result': {
                'results': results
            }
        })

    def perform_action(self, resource):
        if self.kind == "DaemonSet":
            current_revision = resource['metadata']['generation']
        elif self.kind == "Deployment":
            current_revision = resource['metadata']['annotations']['deployment.kubernetes.io/revision']

        managed_resources = self.kubernetes_facts(self.managed_resource['kind'],
                                                  self.managed_resource['api_version'],
                                                  '',
                                                  self.namespace,
                                                  resource['spec']
                                                  ['selector']
                                                  ['matchLabels'],
                                                  '')

        prev_managed_resource = get_previous_revision(managed_resources['resources'],
                                                      current_revision)

        if self.kind == "Deployment":
            del prev_managed_resource['spec']['template']['metadata']['labels']['pod-template-hash']

            resource_patch = [{
                "op": "replace",
                "path": "/spec/template",
                "value": prev_managed_resource['spec']['template']
            }, {
                "op": "replace",
                "path": "/metadata/annotations",
                "value": {
                    "deployment.kubernetes.io/revision": prev_managed_resource['metadata']['annotations']['deployment.kubernetes.io/revision']
                }
            }]

            api_target = 'deployments'
            content_type = 'application/json-patch+json'
        elif self.kind == "DaemonSet":
            resource_patch = prev_managed_resource["data"]

            api_target = 'daemonsets'
            content_type = 'application/strategic-merge-patch+json'

        rollback = self.client.request("PATCH",
                                       "/apis/{0}/namespaces/{1}/{2}/{3}"
                                       .format(self.api_version,
                                               self.namespace,
                                               api_target,
                                               self.name),
                                       body=resource_patch,
                                       content_type=content_type)

        result = {'changed': True, 'result': {}}
        result['method'] = 'patch'
        result['body'] = resource_patch
        result['result'] = rollback.to_dict()
        return result

    @property
    def argspec(self):
        args = copy.deepcopy(AUTH_ARG_SPEC)
        args.update(
            dict(
                kind=dict(required=True),
                api_version=dict(default='apps/v1', aliases=['api', 'version']),
                name=dict(),
                namespace=dict(),
                label_selectors=dict(type='list', elements='str', default=[]),
                field_selectors=dict(type='list', elements='str', default=[]),
            )
        )
        return args


def get_previous_revision(all_resources, current_revision):
    for resource in all_resources:
        if resource['kind'] == 'ReplicaSet':
            if int(resource['metadata']
                   ['annotations']
                   ['deployment.kubernetes.io/revision']) == int(current_revision) - 1:
                return resource
        elif resource['kind'] == 'ControllerRevision':
            if int(resource['metadata']
                   ['annotations']
                   ['deprecated.daemonset.template.generation']) == int(current_revision) - 1:
                return resource
    return None
