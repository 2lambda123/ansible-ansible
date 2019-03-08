# -*- coding: utf-8 -*-
# Copyright (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


from units.compat.mock import Mock
from ansible.module_utils.facts.system.distribution import DistributionFiles
from . distribution_data import DISTRIBUTION_FILE_DATA


def mock_module():
    mock_module = Mock()
    mock_module.params = {'gather_subset': ['all'],
                          'gather_timeout': 5,
                          'filter': '*'}
    mock_module.get_bin_path = Mock(return_value=None)
    return mock_module


def test_parse_distribution_file_clear_linux():
    test_input = {
        'name': 'ClearLinux',
        'data': DISTRIBUTION_FILE_DATA['clearlinux'],
        'path': '/usr/lib/os-release',
        'collected_facts': None,
    }

    result = (
        True,
        {
            'distribution': 'Clear Linux OS',
            'distribution_major_version': '28120',
            'distribution_release': 'clear-linux-os',
            'distribution_version': '28120'
        }
    )

    distribution = DistributionFiles(module=mock_module())
    assert result == distribution.parse_distribution_file_ClearLinux(**test_input)


def test_parse_distribution_file_clear_linux_no_match():
    # Test against data from other distributions that use same file path to
    # ensure we do not get an incorrect match.

    scenarios = [
        {
            'case': {
                'name': 'ClearLinux',
                'data': DISTRIBUTION_FILE_DATA['coreos'],
                'path': '/usr/lib/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
        {
            'case': {
                'name': 'ClearLinux',
                'data': DISTRIBUTION_FILE_DATA['linuxmint'],
                'path': '/usr/lib/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
        {
            'case': {
                'name': 'ClearLinux',
                'data': DISTRIBUTION_FILE_DATA['debian9'],
                'path': '/usr/lib/os-release',
                'collected_facts': None,
            },
            'result': (False, {}),
        },
    ]

    distribution = DistributionFiles(module=mock_module())
    for scenario in scenarios:
        assert scenario['result'] == distribution.parse_distribution_file_ClearLinux(**scenario['case'])
