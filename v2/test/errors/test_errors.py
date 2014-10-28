# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

# Make coding more python3-ish
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.compat.tests import unittest

from ansible.parsing.yaml.objects import AnsibleBaseYAMLObject
from ansible.errors import AnsibleError

from ansible.compat.tests import BUILTINS
from ansible.compat.tests.mock import mock_open, patch

class TestErrors(unittest.TestCase):

    def setUp(self):
        self.message = 'This is the error message'

        self.obj = AnsibleBaseYAMLObject()

    def tearDown(self):
        pass

    def test_basic_error(self):
        e = AnsibleError(self.message)
        self.assertEqual(e.message, self.message)
        self.assertEqual(e.__repr__(), self.message)

    @patch.object(AnsibleError, '_get_error_lines_from_file')
    def test_error_with_object(self, mock_method):
        self.obj._data_source   = 'foo.yml'
        self.obj._line_number   = 1
        self.obj._column_number = 1

        mock_method.return_value = ('this is line 1\n', '')
        e = AnsibleError(self.message, self.obj)

        self.assertEqual(e.message, "This is the error message\nThe error appears to have been in 'foo.yml': line 1, column 1,\nbut may actually be before there depending on the exact syntax problem.\n\nthis is line 1\n^\n")

    def test_get_error_lines_from_file(self):
        m = mock_open()
        m.return_value.readlines.return_value = ['this is line 1\n']

        with patch('{0}.open'.format(BUILTINS), m):
            # this line will be found in the file
            self.obj._data_source   = 'foo.yml'
            self.obj._line_number   = 1
            self.obj._column_number = 1
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(e.message, "This is the error message\nThe error appears to have been in 'foo.yml': line 1, column 1,\nbut may actually be before there depending on the exact syntax problem.\n\nthis is line 1\n^\n")

            # this line will not be found, as it is out of the index range
            self.obj._data_source   = 'foo.yml'
            self.obj._line_number   = 2
            self.obj._column_number = 1
            e = AnsibleError(self.message, self.obj)
            self.assertEqual(e.message, "This is the error message\nThe error appears to have been in 'foo.yml': line 2, column 1,\nbut may actually be before there depending on the exact syntax problem.\n\n(specified line no longer in file, maybe it changed?)")
        
