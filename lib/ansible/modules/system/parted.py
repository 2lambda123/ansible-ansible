#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2016, Fabrizio Colonna <colofabrix@tin.it>
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

import locale
import math

DOCUMENTATION = '''
---
author: "Fabrizio Colonna <colofabrix@tin.it>"
module: parted
short_description: Configure block device partitions
version_added: "2.3"
description:
  - Linux parted tool. For a full description of the fields and the options check the GNU parted manual.
options:
  device:
    description: The block device (disk) where to operate
    required: True
  align:
    description: Set alignment for newly created partitions, valid alignment types are: none, cylinder, minimal and optimal.
    choices: ['none', 'cylinder', 'minimal', 'optimal']
    required: False
    default: optimal
  number:
    description: The number of the partition to work with or the number of the partition that will be created. Required when performing any action on the disk, except fetching information.
    required: False
  unit:
    description: Selects the current default unit that Parted will use to display locations and capacities on the disk and to interpret those given by the user if they are not suffixed by an unit.
    choices: ['s', 'B', 'KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB', 'TB', 'TiB', '%', 'cyl', 'chs', 'compact']
    required: False
    default: KiB
  label:
    description: Creates a new disk label.
    required: False
    default: msdos
  part_type:
    description: Is one of 'primary', 'extended' or 'logical' and may be specified only with 'msdos' or 'dvh' partition tables. A name must be specified for a 'gpt' partition table. Neither part-type nor name may be used with a 'sun' partition table. 
    choices: ['primary', 'extended', 'logical']
    required: False
  part_start:
    description: Where the partition will start as offset from the beginning of the disk, that is, the "distance" from the start of the disk.
    required: False
    default: 0%
  part_end :
    description: Where the partition will end as offset from the beginning of the disk, that is, the "distance" from the start of the disk.
    required: False
    default: 100%
  name:
    description: Sets the name for the partition number (GPT, Mac, MIPS and PC98 only).
    required: False
  flags_on:
    description: A comma-separated list of flags to set for the partition
    required: False
    default: ''
  flags_off:
    description: A comma-separated list of flags to clear for the partition
    required: False
    default: ''
  state:
    description: If to create or delete a partition. If not present or empty the module will return only the device information.
    choices: ['present', 'absent'. '']
    required: False
    default: present
'''

RETURN = '''
partition_info:
  description: Current partition information
  returned: success
  type: dict
  contains:
    generic:
      description: Generic device information
      type: dict
    partitions:
      description: List of device partitions
      type: list
    sample: {
      "partition_info": {
        "generic": {
          "dev": "/dev/sda",
          "logical_block": 512,
          "model": "VMware Virtual disk",
          "physical_block": 512,
          "size": 15728640,
          "table": "msdos"
        },
        "partitions": [{
          "begin": 1024,
          "end": 513024,
          "flags": "boot",
          "fstype": "ext4",
          "num": 1,
          "size": 512000
        }, ...
        ]
      },
      "script": ""
    } 
'''

EXAMPLES = """
- name: Read device information
  parted: device=/dev/sdb
  register: sdb_info

- name: Create a new primary partition
  parted:
    device=/dev/sdb
    number=1
    state=present

- name: Create a new primary partition with a size of 1GiB
  parted:
    device=/dev/sdb
    number=1
    flags_on=lvm
    state=present
    part_end=1GiB

- name: Create a new primary partition for LVM
  parted:
    device=/dev/sdb
    number=1
    flags_on=lvm
    state=present

- name: Remove all LVM partitions from disk
  parted:
    device=/dev/sdb
    number="{{ item.num }}"
    state=absent
  with_items: "{{ sdb_info.partitions }}"
  when: 'lvm' in item.flags
"""


def parse_unit(s, unit, ceil=True):
    """
    Converts '123.1unit' string into ints
    If ceil is True it will be rounded up (124)
    and and down (123) if ceil is False.
    """
    flt = locale.atof(s.lower().split(unit.lower())[0])
    if ceil:
        return int(math.ceil(flt))
    return int(math.floor(flt))


def parse_partition_info(output, unit):
    """
    Parses the output of parted and transforms the data into
    a dictionary.

    Parted Machine Parseable Output:
     - All lines end with a semicolon (;)
     - The first line indicates the units in which the output is expressed.
       CHS, CYL and BYT stands for CHS, Cylinder and Bytes respectively.
     - The second line is made of disk information in the following format:
       "path":"size":"transport-type":"logical-sector-size":"physical-sector-size":"partition-table-type":"model-name";
     - If the first line was either CYL or CHS, the next line will contain
       information on no. of cylinders, heads, sectors and cylinder size.
     - Partition information begins from the next line. This is of the format:
       (for BYT)
       "number":"begin":"end":"size":"filesystem-type":"partition-name":"flags-set";
       (for CHS/CYL)
       "number":"begin":"end":"filesystem-type":"partition-name":"flags-set";
    """
    lines = output.split('\n')
    generic_params = lines[1].rstrip(';').split(':')
    generic = {
        'dev':   generic_params[0],
        'size':  parse_unit(generic_params[1], unit),
        'logical_block':  int(generic_params[3]),
        'physical_block': int(generic_params[4]),
        'table': generic_params[5],
        'model': generic_params[6]
    }

    parts = []
    for line in lines[2:]:
        line = line.strip().rstrip(';')
        if not line:
            continue

        part_params = line.split(':')
        parts.append({
            'num':    int(part_params[0]),
            'begin':  parse_unit(part_params[1], unit),
            'end':    parse_unit(part_params[2], unit),
            'size':   parse_unit(part_params[3], unit),
            'fstype': part_params[4] or None,
            'flags':  part_params[6] or None,
        })

    return { 'generic': generic, 'partitions': parts }


def get_device_info(device, unit):
    """
    Fetches information about a disk and its partitions and it
    returns a dictionary.
    """
    global module

    command = "parted -s -m {0} -- unit '{1}' print".format(device, unit)
    rc, out, err = module.run_command(command)

    if rc != 0 and 'unrecognised disk label' not in err.lower():
        module.fail_json(
            msg="Error while getting device information with parted script: '{0}'".format(command),
            rc=rc, out=out, err=err
        )

    out = parse_partition_info(out, unit)
    return out


def part_exists(partitions, attribute, number):
    """
    Looks if a partition that has a specific value for a specific
    attribute actually exists.
    """
    return any(
        part[attribute] and
        part[attribute] == number for part in partitions
    )


def parted(script, device, align):
    """
    Runs a parted script.
    """
    global module

    if script:
        command = "parted -s -m -a {0} {1} -- {2}".format(align, device, script)
        rc, out, err = module.run_command(command)

        if rc != 0:
            module.fail_json(
                msg="Error while running parted script: '{0}'".format(command.strip()),
                rc=rc, out=out, err=err
            )


def main():
    global module
    changed = False; script = ""; output_script = ""

    module = AnsibleModule(
        argument_spec = dict(
            device     = dict(required=True),
            align      = dict(default='optimal', choices=['none', 'cylinder', 'minimal', 'optimal'], required=False),
            number     = dict(default=-1, type='int', required=False),
            # unit <unit> command
            unit       = dict(default='KiB', choices=['s', 'B', 'KB', 'KiB', 'MB', 'MiB', 'GB', 'GiB', 'TB', 'TiB', '%', 'cyl', 'chs', 'compact'], required=False),
            # mklabel <label-type> command
            label      = dict(default='', choices=['aix', 'amiga', 'bsd', 'dvh', 'gpt', 'loop', 'mac', 'msdos', 'pc98', 'sun', ''], required=False),
            # mkpart <part-type> [<fs-type>] <start> <end> command
            part_type  = dict(default='primary', choices=['primary', 'extended', 'logical'], required=False),
            part_start = dict(default='0%', type='str', required=False),
            part_end   = dict(default='100%', type='str', required=False),
            # name <partition> <name> command
            name       = dict(default='', type='str', required=False),
            # set <partition> <flag> <state> command
            flags_on   = dict(default='', type='str', required=False),
            flags_off  = dict(default='', type='str', required=False),
            # rm/mkpart command
            state      = dict(default='', choices=['present', 'absent', ''], required=False)
        ),
        required_together = [
            ['state', 'number'],
            ['part_type', 'part_start', 'part_end', 'number'],
            ['name', 'number'],
            ['flags_on', 'number'],
            ['flags_off', 'number']
        ]
    )

    # Data extraction
    device     = module.params['device']
    align      = module.params['align'].lower()
    number     = module.params['number']
    unit       = module.params['unit']
    label      = module.params['label'].lower()
    part_type  = module.params['part_type'].lower()
    part_start = module.params['part_start']
    part_end   = module.params['part_end']
    name       = module.params['name']
    flags_on   = module.params['flags_on'].lower().split(',')
    flags_off  = module.params['flags_off'].lower().split(',')
    state      = module.params['state'].lower()

    # Read the current disk information
    current_device = get_device_info(device, unit)
    current_parts = current_device['partitions']

    if state == 'present':
        # Default value for the label
        if not current_device['generic']['table'] or \
           current_device['generic']['table'] == 'unknown' and \
           not label:
            label = 'msdos'

        # Assign label if required
        if label:
            script += "mklabel {0} ".format(label)

        # Create partition if required
        if part_type and not part_exists(current_parts, 'num', number):
            script += "mkpart {0} {1} {2} ".format(part_type, part_start, part_end)

        # Set the unit of the run
        if unit and script:
            script = "unit {0} ".format(unit) + script

        # Execute the script and update the data structure
        # This will create the partition for the next steps
        if script:
            output_script += script
            parted(script, device, align)
            changed = True; script = ""

            current_parts = get_device_info(device, unit)['partitions']

        if part_exists(current_parts, 'num', number):
            # Assign name to the the partition
            if name and name in ['gpt', 'mac', 'mips', 'pc98']:
                script += "name {0} {1} ".format(number, name)

            # Flags to set
            for flag in flags_on:
                if flag and not part_exists(current_parts, 'flags', flag):
                    script += "set {0} {1} on ".format(number, flag)

            # Flags to clear
            for flag in flags_off:
                if flag and part_exists(current_parts, 'flags', flag):
                    script += "set {0} {1} off ".format(number, flag)

        # Set the unit of the run
        if unit and script:
            script = "unit {0} ".format(unit) + script

        # Execute the script
        if script:
            output_script += script; changed = True
            parted(script, device, align)

    elif state == 'absent':
        # Remove the partition
        if part_exists(current_parts, 'num', number):
            script = "rm {0} ".format(number)
            output_script += script; changed = True
            parted(script, device, align)

    # Final status of the device
    final_device_status = get_device_info(device, unit)
    module.exit_json(
        changed=changed,
        partition_info=final_device_status,
        script=output_script.strip()
    )


from ansible.module_utils.basic import *

if __name__ == '__main__':                                                                          
    main() 

