#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
#
# Copyright (C) 2017 Lenovo, Inc.
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
# Module to Rollback Config back to Lenovo Switches
#
# Lenovo Networking
#

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: cnos_rollback
author: "Dave Kasberg (@dkasberg)"
short_description: Roll back the running or startup configuration from a remote server on devices running Lenovo CNOS
description:
    - This module allows you to work with switch configurations. It provides a way to roll back configurations
     of a switch from a remote server. This is achieved by using startup or running configurations of the target
     device that were previously backed up to a remote server using FTP, SFTP, TFTP, or SCP.
     The first step is to create a directory from where the remote server can be reached. The next step is to
     provide the full file path of the backup configuration's location. Authentication details required by the
     remote server must be provided as well.
     By default, this method overwrites the switch's configuration file with the newly downloaded file.
     This module uses SSH to manage network device configuration.
     The results of the operation will be placed in a directory named 'results'
     that must be created by the user in their local directory to where the playbook is run.
     For more information about this module from Lenovo and customizing it usage for your
     use cases, please visit U(http://systemx.lenovofiles.com/help/index.jsp?topic=%2Fcom.lenovo.switchmgt.ansible.doc%2Fcnos_rollback.html)
version_added: "2.3"
extends_documentation_fragment: cnos
options:
   configType:
        description:
            - This refers to the type of configuration which will be used for the rolling back process.
             The choices are the running or startup configurations. There is no default value, so it will result
             in an error if the input is incorrect.
        required: Yes
        default: Null
        choices: [running-config, startup-config]
   protocol:
        description:
            - This refers to the protocol used by the network device to interact with the remote server from where to
             download the backup configuration. The choices are FTP, SFTP, TFTP, or SCP. Any other protocols will result
             in error. If this parameter is not specified, there is no default value to be used.
        required: Yes
        default: Null
        choices: [SFTP, SCP, FTP, TFTP]
   rcserverip:
        description:
            - This specifies the IP Address of the remote server from where the backup configuration will be downloaded.
        required: Yes
        default: Null
   rcpath:
        description:
            - This specifies the full file path of the configuration file located on the remote server. In case the relative
             path is used as the variable value, the root folder for the user of the server needs to be specified.
        required: Yes
        default: Null
   serverusername:
        description:
            - Specify the username for the server relating to the protocol used.
        required: Yes
        default: Null
   serverpassword:
        description:
            - Specify the password for the server relating to the protocol used.
        required: Yes
        default: Null
'''
EXAMPLES = '''
Tasks : The following are examples of using the module cnos_rollback. These are written in the main.yml file of the tasks directory.
---

- name: Test Rollback of config - Running config
  cnos_rolback:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_rollback_{{ inventory_hostname }}_output.txt"
      configType: running-config
      protocol: "sftp"
      serverip: "10.241.106.118"
      rcpath: "/root/cnos/G8272-running-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Rollback of config - Startup config
  cnos_rolback:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_rollback_{{ inventory_hostname }}_output.txt"
      configType: startup-config
      protocol: "sftp"
      serverip: "10.241.106.118"
      rcpath: "/root/cnos/G8272-startup-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Rollback of config - Running config - TFTP
  cnos_rolback:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_rollback_{{ inventory_hostname }}_output.txt"
      configType: running-config
      protocol: "tftp"
      serverip: "10.241.106.118"
      rcpath: "/anil/G8272-running-config.txt"
      serverusername: "root"
      serverpassword: "root123"

- name: Test Rollback of config - Startup config - TFTP
  cnos_rolback:
      host: "{{ inventory_hostname }}"
      username: "{{ hostvars[inventory_hostname]['username'] }}"
      password: "{{ hostvars[inventory_hostname]['password'] }}"
      deviceType: "{{ hostvars[inventory_hostname]['deviceType'] }}"
      enablePassword: "{{ hostvars[inventory_hostname]['enablePassword'] }}"
      outputfile: "./results/test_rollback_{{ inventory_hostname }}_output.txt"
      configType: startup-config
      protocol: "tftp"
      serverip: "10.241.106.118"
      rcpath: "/anil/G8272-startup-config.txt"
      serverusername: "root"
      serverpassword: "root123"

'''
RETURN = '''
msg:
  description: Success or failure message
  returned: always
  type: string
  sample: "Config file tranferred to Device"
'''

import sys
try:
    import paramiko
    HAS_PARAMIKO=True
except ImportError:
    HAS_PARAMIKO=False
import time
import argparse
import socket
import array
import json
import time
import re
try:
    from ansible.module_utils import cnos
    HAS_LIB = True
except:
    HAS_LIB = False
from ansible.module_utils.basic import AnsibleModule
from collections import defaultdict


def main():
    module = AnsibleModule(
        argument_spec=dict(
            outputfile=dict(required=True),
            host=dict(required=True),
            username=dict(required=True),
            password=dict(required=True, no_log=True),
            enablePassword=dict(required=False, no_log=True),
            deviceType=dict(required=True),
            configType=dict(required=True),
            protocol=dict(required=True),
            serverip=dict(required=True),
            rcpath=dict(required=True),
            serverusername=dict(required=False),
            serverpassword=dict(required=False, no_log=True),),
        supports_check_mode=False)

    username = module.params['username']
    password = module.params['password']
    enablePassword = module.params['enablePassword']
    outputfile = module.params['outputfile']
    host = module.params['host']
    deviceType = module.params['deviceType']
    configType = module.params['configType']
    protocol = module.params['protocol'].lower()
    rcserverip = module.params['serverip']
    rcpath = module.params['rcpath']
    serveruser = module.params['serverusername']
    serverpwd = module.params['serverpassword']
    output = ""
    timeout = 90
    tftptimeout = 450
    if not HAS_PARAMIKO:
        module.fail_json(msg='paramiko is required for this module')

    # Create instance of SSHClient object
    remote_conn_pre = paramiko.SSHClient()

    # Automatically add untrusted hosts (make sure okay for security policy in your environment)
    remote_conn_pre.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # initiate SSH connection with the switch
    remote_conn_pre.connect(host, username=username, password=password)
    time.sleep(2)

    # Use invoke_shell to establish an 'interactive session'
    remote_conn = remote_conn_pre.invoke_shell()
    time.sleep(2)

    # Enable and enter configure terminal then send command
    output = output + cnos.waitForDeviceResponse("\n", ">", 2, remote_conn)

    output = output + cnos.enterEnableModeForDevice(enablePassword, 3, remote_conn)

    # Make terminal length = 0
    output = output + cnos.waitForDeviceResponse("terminal length 0\n", "#", 2, remote_conn)

    # Invoke method for Config transfer from server
    if(configType == 'running-config'):
        if(protocol == "tftp" or protocol == "ftp"):
            transfer_status = cnos.doRunningConfigRollback(protocol, tftptimeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        elif(protocol == "sftp" or protocol == "scp"):
            transfer_status = cnos.doSecureRunningConfigRollback(protocol, timeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        else:
            transfer_status = "Invalid Protocol option"
    elif(configType == 'startup-config'):
        if(protocol == "tftp" or protocol == "ftp"):
            transfer_status = cnos.doStartUpConfigRollback(protocol, tftptimeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        elif(protocol == "sftp" or protocol == "scp"):
            transfer_status = cnos.doSecureStartUpConfigRollback(protocol, timeout, rcserverip, rcpath, serveruser, serverpwd, remote_conn)
        else:
            transfer_status = "Invalid Protocol option"
    else:
        transfer_status = "Invalid configType Option"

    output = output + "\n Config Transfer status \n" + transfer_status

    # Save it into the file
    file = open(outputfile, "a")
    file.write(output)
    file.close()

    # need to add logic to check when changes occur or not
    errorMsg = cnos.checkOutputForError(output)
    if(errorMsg is None):
        module.exit_json(changed=True, msg="Config file tranferred to Device")
    else:
        module.fail_json(msg=errorMsg)

if __name__ == '__main__':
        main()
