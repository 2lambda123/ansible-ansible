#!/usr/bin/python
# GNU General Public License v3.0+ (see COPYING or
# https://www.gnu.org/licenses/gpl-3.0.txt)
#
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'supported_by': 'community',
    'status': ['preview']
}


DOCUMENTATION = '''
---
version_added: "1.1"
author:
  - Naval Patel (@navalkp)
  - Prashant Bhosale (@prabhosa)
module: lxca_cmms
short_description: Custom module for lxca cmms inventory utility
description:
  - This module returns/displays a inventory details of cmms

options:
  uuid:
    description:
      uuid of device, this is string with length greater than 16.

  command_options:
    description:
      options to filter nodes information
    default: cmms
    choices:
        - cmms
        - cmms_by_uuid
        - cmms_by_chassis_uuid

  chassis:
    description:
      uuid of chassis, this is string with length greater than 16.

extends_documentation_fragment:
    - lxca_common
'''

EXAMPLES = '''
# get all cmms info
- name: get nodess data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"

# get specific cmms info by uuid
- name: get nodes data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    uuid: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: cmms_by_uuid

# get specific cmms info by chassis uuid
- name: get nodes data from LXCA
  lxca_cmms:
    login_user: USERID
    login_password: Password
    auth_url: "https://10.243.15.168"
    chassis: "3C737AA5E31640CE949B10C129A8B01F"
    command_options: cmms_by_chassis_uuid

'''


import traceback
from ansible.module_utils.remote_management.lxca_common import LXCAModuleBase
from pylxca import cmms


class CmmsModule(LXCAModuleBase):
    '''
    This class fetch information about nodes in lxca
    '''

    UUID_REQUIRED = 'UUID of device is required for nodes_by_uuid command.'
    CHASSIS_UUID_REQUIRED = 'UUID of chassis is required for cmms_by_chassis_uuid command.'
    SUCCESS_MSG = "Success %s result"

    def __init__(self):
        self.func_dict = {
            'cmms': self._cmms,
            'cmms_by_uuid': self._cmms_by_uuid,
            'cmms_by_chassis_uuid': self._cmms_by_chassis_uuid,
        }
        args_spec = dict(
            command_options=dict(default='cmms', choices=list(self.func_dict)),
            uuid=dict(default=None), chassis=dict(default=None)
        )
        super(CmmsModule, self).__init__(input_args_spec=args_spec)
        self._changed = False

    def execute_module(self):
        try:
            result = self.func_dict[self.module.params['command_options']]()
            return dict(changed=self._changed,
                        msg=self.SUCCESS_MSG % self.module.params['command_options'],
                        result=result)

        except Exception as exception:
            error_msg = '; '.join((e) for e in exception.args)
            self.module.fail_json(msg=error_msg, exception=traceback.format_exc())

    def _cmms(self):
        return cmms(self.lxca_con)

    def _cmms_by_uuid(self):
        if not self.module.params['uuid']:
            self.module.fail_json(msg=self.UUID_REQUIRED)
        return cmms(self.lxca_con, self.module.params['uuid'])

    def _cmms_by_chassis_uuid(self):
        if not self.module.params['chassis']:
            self.module.fail_json(msg=self.CHASSIS_UUID_REQUIRED)
        return cmms(self.lxca_con, chassis=self.module.params['chassis'])


def main():
    CmmsModule().run()


if __name__ == '__main__':
    main()
