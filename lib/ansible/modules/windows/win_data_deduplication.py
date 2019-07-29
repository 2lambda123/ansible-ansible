#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019 github@rnsc.be
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: win_data_deduplication
version_added: "2.9"
short_description: Module to enable Data Deduplication on a volume.
description:
- This module can be used to enable Data Deduplication on a Windows volume.
- You have to have the FS-Data-Deduplication feature installed.
- This module doesn't support check_mode due to a lack of WhatIf support.
- Windows 2012 R2 and lower require a reboot for the feature to be active.
options:
  drive_letter:
    description:
    - Windows drive letter on which to enable data deduplication.
    required: yes
    type: str
  enabled:
    description:
    - Wether to enable or disable data deduplication on the selected volume.
    required: yes
    default: true
    type: bool
  settings:
    description:
    - List of settings to pass to the Set-DedupVolume powershell command.
    - Please see the Microsoft Powershell for Windows documentation for all the available options.
    - MinimumFileSize will default to 32768 if not defined or if the value is less than 32768.
    required: no
    type: list
  dedup_job:
    description:
    - Start a dedup job immediately.
    - Type parameter is mandatory in case you want to run a dedup job.
    - Please see the Microsoft Powershell for Windows documentation for all the available options.
    - This option is not idempotent.
    required: no
    type: list
author:
- rnsc (@rnsc)
'''

EXAMPLES = r'''
# Playbook example
---
- name: Set volume deduplication
  hosts: all
  gather_facts: false
  tasks:
    - name: FS-Data-Deduplication
      win_feature:
        name: FS-Data-Deduplication
        include_sub_features: true
        state: present
    - name: Enable Data Deduplication on D
      win_data_deduplication:
        drive_letter: 'D'
        enabled: true
        settings:
          - NoCompress: true
          - MinimumFileAgeDays: 1
          - MinimumFileSize: 0
        dedup_job:
          - Type: 'Optimization'
'''
