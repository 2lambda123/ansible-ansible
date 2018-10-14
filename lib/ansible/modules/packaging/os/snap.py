#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Stanislas Lange (angristan) <angristan@pm.me>
# Copyright: (c) 2018, Victor Carceler <vcarceler@iespuigcastellar.xeill.net>

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: snap

short_description: Manages snaps

version_added: "2.8"

description:
    - "Manages snaps packages."

options:
    name:
        description:
            - Name of the snap to install or remove. Can be a list of snaps.
        required: true
    state:
        description:
            - Desired state of the package.
        required: false
        default: present
        choices: [ absent, present ]
    classic:
        description:
            - Confinement policy. The classic confinment allows a snap to have
              the same level of access to the system as "classic" packages,
              like those managed by APT. This option corresponds to the --classic argument.
        type: bool
        required: false
        default: False
    channel:
        description:
            - Define which release of a snap is installed and tracked for updates.
        type: str
        required: false
        default: stable

author:
    - Victor Carceler (vcarceler@iespuigcastellar.xeill.net)
    - Stanislas Lange (angristan) <angristan@pm.me>
'''

EXAMPLES = '''
# Install "foo" and "bar" snap
- name: Install foo
  snap:
    name:
      - foo
      - bar

# Remove "foo" snap
- name: Remove foo
  snap:
    name: foo
    state: absent

# Install a snap with classic confinement
- name: Install "foo" with option --classic
  snap:
    name: foo
    classic: yes

# Install a snap with from a specific channel
- name: Install "foo" with option --channel=latest/edge
  snap:
    name: foo
    channel: latest/edge
'''

RETURN = '''
classic:
    description: Whether or not the snaps were installed with the classic confinement
    type: boolean
    returned: When snaps are installed
channel:
    description: The channel the snaps were installed from
    type: string
    returned: When snaps are installed
cmd:
    description: The command that was executed on the host
    type: string
    returned: When changed is true
snaps_installed:
    description: The list of actually installed snaps
    type: list
    returned: When any snaps have been installed
snaps_removed:
    description: The list of actually removed snaps
    type: list
    returned: When any snaps have been removed
'''

import operator
import re

from ansible.module_utils.basic import AnsibleModule


def snap_exists(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'info', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc == 0


def is_snap_installed(module, snap_name):
    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'list', snap_name]
    cmd = ' '.join(cmd_parts)
    rc, out, err = module.run_command(cmd, check_rc=False)

    return rc == 0


def get_snap_for_action(module):
    """Construct a list of snaps to use for current action."""
    snaps = module.params['name']

    is_present_state = module.params['state'] == 'present'
    negation_predicate = bool if is_present_state else operator.not_

    def predicate(s):
        return negation_predicate(is_snap_installed(module, s))

    return [s for s in snaps if predicate(s)]


def install_snaps(module, snap_names):
    exit_kwargs = {
        'classic': module.params['classic'],
        'channel': module.params['channel'],
        'changed': False,
    }

    snaps_not_installed = get_snap_for_action(module)
    if not snaps_not_installed:
        module.exit_json(**exit_kwargs)

    if module.check_mode:
        exit_kwargs['changed'] = True
        exit_kwargs['snaps_installed'] = snaps_not_installed
        module.exit_json(**exit_kwargs)

    classic = ['--classic'] if module.params['classic'] else []
    channel = ['--channel ', module.params['channel']]

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'install'] + snaps_not_installed + classic + channel
    cmd = ' '.join(cmd_parts)

    # Actually install the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        exit_kwargs['changed'] = True
        exit_kwargs['snaps_installed'] = snaps_not_installed
        module.exit_json(cmd=cmd, stdout=out, stderr=err, **exit_kwargs)
    else:
        msg = "Ooops! Snap installation failed while executing '{cmd}', please examine logs and error output for more details.".format(cmd=cmd)
        m = re.match(r'^error: This revision of snap "(?P<package_name>\w+)" was published using classic confinement', err)
        if m is not None:
            err_pkg = m.group('package_name')
            msg = "Couldn't install {name} because it requires classic confinement".format(name=err_pkg)
        module.fail_json(msg=msg, cmd=cmd, stdout=out, stderr=err, **exit_kwargs)


def remove_snaps(module, snap_names):
    snaps_installed = get_snap_for_action(module)
    if not snaps_installed:
        module.exit_json(changed=False)

    if module.check_mode:
        module.exit_json(changed=True, snaps_removed=snaps_installed)

    snap_path = module.get_bin_path("snap", True)
    cmd_parts = [snap_path, 'remove'] + snaps_installed
    cmd = ' '.join(cmd_parts)

    # Actually remove the snaps
    rc, out, err = module.run_command(cmd, check_rc=False)

    if rc == 0:
        module.exit_json(changed=True, snaps_removed=snaps_installed, cmd=cmd, stdout=out, stderr=err)
    else:
        msg = "Ooops! Snap removal failed while executing '{cmd}', please examine logs and error output for more details.".format(cmd=cmd)
        module.fail_json(msg=msg, cmd=cmd, stdout=out, stderr=err)


def main():
    module_args = {
        'name': dict(type='list', required=True),
        'state': dict(type='str', required=False, default='present', choices=['absent', 'present']),
        'classic': dict(type='bool', required=False, default=False),
        'channel': dict(type='str', required=False, default='stable'),
    }
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
    )
    state = module.params['state']

    # Check if snaps are valid
    for snap_name in module.params['name']:
        if not snap_exists(module, snap_name):
            module.fail_json(msg="No snap matching '%s' available." % snap_name)

    # Apply changes to the snaps
    action_map = {
        'present': install_snaps,
        'absent': remove_snaps,
    }
    action_map[state](module)


if __name__ == '__main__':
    main()
