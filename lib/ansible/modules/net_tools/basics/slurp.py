#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['stableinterface'],
                    'supported_by': 'core'}

DOCUMENTATION = r'''
---
module: slurp
version_added: historical
short_description: Slurps a file from remote nodes
description:
     - This module works like M(fetch). It is used for fetching a base64-
       encoded blob containing the data in a remote file.
     - This module is also supported for Windows targets.
options:
  src:
    description:
      - The file on the remote system to fetch. This I(must) be a file, not a directory.
    type: path
    required: true
    aliases: [ path ]
notes:
   - This module returns an 'in memory' base64 encoded version of the file, take into account that this will require at least twice the RAM as the
     original file size.
   - This module is also supported for Windows targets.
seealso:
- module: fetch
author:
    - Ansible Core Team
    - Michael DeHaan (@mpdehaan)
'''

EXAMPLES = r'''
- name: Find out what the remote machine's mounts are
  slurp:
    src: /proc/mounts
  register: mounts

- debug:
    msg: "{{ mounts['content'] | b64decode }}"

# From the commandline, find the pid of the remote machine's sshd
# $ ansible host -m slurp -a 'src=/var/run/sshd.pid'
# host | SUCCESS => {
#     "changed": false,
#     "content": "MjE3OQo=",
#     "encoding": "base64",
#     "source": "/var/run/sshd.pid"
# }
# $ echo MjE3OQo= | base64 -d
# 2179
'''

import binascii
import hashlib
import io
import os

from functools import partial

from ansible.module_utils._text import to_native
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.six import PY3


MAXLINESIZE = 76  # Excluding the CRLF
MAXBINSIZE = (MAXLINESIZE//4)*3


def b64encode_and_checksum(filename, output):
    '''Read and base64 encode small blocks of a file,
    while also calculating the sha1 sum of the data

    This code is inspired by ``base64.encode``

    :arg filename: Filename to be read, encoded, and hashed
    :arg output: File handle to stream base64 encoded data to
    :return: sha1 checksum
    '''

    digest = hashlib.sha1()
    with open(to_bytes(filename, errors='surrogate_or_strict'), 'rb') as f:
        for b_block in iter(partial(f.read, MAXBINSIZE), b''):
            output.write(
                binascii.b2a_base64(b_block)
            )
            digest.update(b_block)
    return digest.hexdigest()


def main():
    module = AnsibleModule(
        argument_spec=dict(
            src=dict(type='path', required=True, aliases=['path']),
        ),
        supports_check_mode=True,
    )
    source = module.params['src']

    if not os.path.exists(source):
        module.fail_json(msg="file not found: %s" % source)
    if os.path.isdir(source):
        module.fail_json(msg="path is a directory: %s" % source)
    if not os.access(source, os.R_OK):
        module.fail_json(msg="file is not readable: %s" % source)

    with io.BytesIO() as f:
        checksum = b64encode_and_checksum(source, f)
        data = to_native(f.getvalue()).strip()

    module.exit_json(content=data, source=source, encoding='base64', checksum=checksum)


if __name__ == '__main__':
    main()
