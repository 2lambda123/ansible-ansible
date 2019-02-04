# -*- coding: utf-8 -*-
# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
# (c) 2016 Toshio Kuratomi <tkuratomi@ansible.com>
# (c) 2017-2018 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import pytest

from ansible.module_utils.common.validation import count_terms

TEST_CHECKS = [
    (['state'], 1),
    (['ghost'], 0),
    (['state', 'delay', 'name', 'bob'], 3),
]


@pytest.fixture
def module_params():
    return {
        'state': 'absent',
        'delay': 30,
        'name': 'vim',
    }


@pytest.mark.parametrize('checks', TEST_CHECKS)
def test_count_terms(checks, module_params):
    assert count_terms(checks[0], module_params) == checks[1]
