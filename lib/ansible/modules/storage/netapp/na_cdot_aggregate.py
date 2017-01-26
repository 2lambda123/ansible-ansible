#!/usr/bin/python

# (c) 2016, NetApp, Inc
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
#

DOCUMENTATION = '''

module: na_cdot_aggregate

short_description: Manage NetApp cDOT aggregates
extends_documentation_fragment:
    - netapp.ontap
version_added: '2.3'
author: Sumit Kumar (sumit4@netapp.com)

description:
- Create or destroy aggregates on NetApp cDOT

options:

  state:
    required: true
    description:
    - Whether the specified aggregate should exist or not.
    choices: ['present', 'absent']

  name:
    required: true
    description:
    - The name of the aggregate to manage

  new_name:
    required: false
    description:
    - Rename the aggregate

  disk_count:
    required: false
    notes: required when state == 'present'
    description:
    - Number of disks to place into the aggregate, including parity disks. The disks in this newly-created aggregate come from the spare disk pool. The smallest disks in this pool join the aggregate first, unless the "disk-size" argument is provided. Either "disk-count" or "disks" must be supplied. Range [0..2^31-1].

'''

EXAMPLES = """
    - name: Manage Aggregates
          na_cdot_aggregate:
            state: present
            name: ansibleAggr
            disk_count: 1
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

    - name: Manage Aggregates
          na_cdot_aggregate:
            state: present
            name: ansibleAggr
            new_name: ansibleAggrRenamed
            hostname: "{{ netapp_hostname }}"
            username: "{{ netapp_username }}"
            password: "{{ netapp_password }}"

"""

RETURN = """
msg:
    description: Successfully created new aggregate (if not already available)
    returned: success
    type: string
    sample: '{"changed": true}'

msg:
    description: Successfully renamed aggregate
    returned: success
    type: string
    sample: '{"changed": true}'

"""

import logging
from traceback import format_exc

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.pycompat24 import get_exception
import ansible.module_utils.netapp as netapp_utils

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

HAS_NETAPP_LIB = netapp_utils.has_netapp_lib()

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class NetAppCDOTAggregate(object):

    def __init__(self):
        logger.debug('Init %s', self.__class__.__name__)

        self.argument_spec = netapp_utils.ontap_sf_host_argument_spec()
        self.argument_spec.update(dict(
                state=dict(required=True, choices=['present', 'absent']),
                name=dict(required=True, type='str'),
                new_name=dict(required=False, type='str', default=None),
                disk_count=dict(required=False, type='int'),
            ))

        self.module = AnsibleModule(
            argument_spec=self.argument_spec,
            required_if=[
                ('state', 'present', ['disk_count'])
            ],
            supports_check_mode=True
        )

        p = self.module.params

        # set up state variables
        self.state = p['state']
        self.name = p['name']
        self.new_name = p['new_name']
        self.disk_count = p['disk_count']

        if HAS_NETAPP_LIB is False:
            self.module.fail_json("Unable to import the NetApp-Lib module")
        else:
            self.server = netapp_utils.setup_ontap_zapi(module=self.module)

    def get_aggr(self):
        """
        Checks if aggregate exists.

        :return:
            True if aggregate found
            False if aggregate is not found
        :rtype: bool
        """

        aggr_get_iter = netapp_utils.zapi.NaElement('aggr-get-iter')
        query_details = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-attributes', **{'aggregate-name': self.name})

        query = netapp_utils.zapi.NaElement('query')
        query.add_child_elem(query_details)
        aggr_get_iter.add_child_elem(query)

        try:
            result = self.server.invoke_successfully(aggr_get_iter,
                                                     enable_tunneling=False)
        except netapp_utils.zapi.NaApiError:
            # Error 13040 denotes an aggregate not being found.
            e = get_exception()
            if str(e.code) == "13040":
                return False
            else:
                raise

        if (result.get_child_by_name('num-records') and
                int(result.get_child_content('num-records')) >= 1):
            return True
        else:
            return False

    def create_aggr(self):
        logger.debug('Creating aggregate %s', self.name)

        aggr_create = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-create', **{'aggregate': self.name,
                              'disk-count': str(self.disk_count)})

        try:
            self.server.invoke_successfully(aggr_create,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError:
            e = get_exception()
            logger.exception('Error provisioning aggregate %s. Error code: '
                             '%s', self.name, str(e.code))
            raise

    def delete_aggr(self):
        logger.debug('Removing aggregate %s', self.name)

        aggr_destroy = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-destroy', **{'aggregate': self.name})

        try:
            self.server.invoke_successfully(aggr_destroy,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError:
            e = get_exception()
            logger.exception('Error removing aggregate %s', self.name)
            raise

    def rename_aggregate(self):
        aggr_rename = netapp_utils.zapi.NaElement.create_node_with_children(
            'aggr-rename', **{'aggregate': self.name,
                              'new-aggregate-name':
                                  self.new_name})

        try:
            self.server.invoke_successfully(aggr_rename,
                                            enable_tunneling=False)
        except netapp_utils.zapi.NaApiError:
            e = get_exception()
            logger.exception(
                'Error renaming aggregate %s. Error code: '
                '%s', self.name, str(e.code))
            raise

    def apply(self):
        changed = False
        aggregate_exists = self.get_aggr()
        rename_aggregate = False

        # check if anything needs to be changed (add/delete/update)

        if aggregate_exists:
            if self.state == 'absent':
                logger.debug(
                    "CHANGED: aggregate exists, but requested state is "
                    "'absent'")
                changed = True

            elif self.state == 'present':
                if self.new_name is not None and not self.new_name ==\
                        self.name:
                    logger.debug(
                        "CHANGED: renaming aggregate")
                    rename_aggregate = True
                    changed = True

        else:
            if self.state == 'present':
                logger.debug(
                    "CHANGED: aggregate does not exist, but requested state is"
                    "'present'")

                changed = True

        if changed:
            if self.module.check_mode:
                logger.debug('skipping changes due to check mode')
            else:
                if self.state == 'present':
                    if not aggregate_exists:
                        self.create_aggr()

                    else:
                        if rename_aggregate:
                            self.rename_aggregate()

                elif self.state == 'absent':
                    self.delete_aggr()
        else:
            logger.debug("exiting with no changes")

        self.module.exit_json(changed=changed)


def main():
    v = NetAppCDOTAggregate()

    try:
        v.apply()
    except Exception:
        e = get_exception()
        logger.debug("Exception in apply(): \n%s" % format_exc(e))
        raise

if __name__ == '__main__':
    main()
