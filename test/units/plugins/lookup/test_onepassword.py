# (c) 2018 Scott Buchanan <sbuchanan@ri.pn>
# (c) 2016 Andrew Zenk <azenk@umn.edu> (test_lastpass.py used as starting point)
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

import json
import datetime
from urllib.parse import urlparse
from argparse import ArgumentParser

from nose.plugins.skip import SkipTest

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible.errors import AnsibleError
from ansible.module_utils import six

try:
    import jq
except ImportError:
    raise SkipTest("test_onepassword.py requires the python module 'jq'")

from ansible.plugins.lookup.onepassword import LookupModule, OnePass, OnePassException


# Intentionally excludes metadata leaf nodes that would exist in real output if not relevant.
MOCK_ENTRIES = [
    {
        'vault_name': 'Acme "Quot\'d" Servers',
        'queries': [
            '0123456789',
            'Mock "Quot\'d" Server'
        ],
        'output': {
            'uuid': '0123456789',
            'vaultUuid': '2468',
            'overview': {
                'title': 'Mock "Quot\'d" Server'
            },
            'details': {
                'sections': [{
                    'fields': [
                        { 't': 'username', 'v': 'jamesbond' },
                        { 't': 'password', 'v': 't0pS3cret' },
                        { 't': 'notes', 'v': 'Test note with\nmultiple lines and trailing space.\n\n' },
                        { 't': 'tricksy "quot\'d" field\\', 'v': '"quot\'d" value' }
                    ]
                }]
            }
        }
    },
    {
        'vault_name': 'Acme Logins',
        'queries': [
            '9876543210',
            'Mock Website',
            'acme.com'
        ],
        'output': {
            'uuid': '9876543210',
            'vaultUuid': '2468',
            'overview': {
                'title': 'Mock Website',
                'URLs': [
                    { 'l': 'website', 'u': 'https://acme.com/login' }
                ]
            },
            'details': {
                'sections': [{
                    'fields': [
                        { 't': 'password', 'v': 't0pS3cret' }
                    ]
                }]
            }
        }
    },
]


def get_mock_query_generator(require_field=None):
    for entry in MOCK_ENTRIES:
        for query in entry['queries']:
            for section in entry['output']['details']['sections']:
                for field in section['fields']:
                    if require_field is None or field['t'] == require_field:
                        yield entry, query, field


def get_one_mock_query(require_field=None):
    generator = get_mock_query_generator(require_field)
    return next(generator, None)


class MockOnePass(OnePass):

    _mock_logged_out = False
    _mock_timed_out = False

    def _lookup_mock_entry(self, key, vault=None):
        for entry in MOCK_ENTRIES:
            if vault is not None and vault != entry['vault_name'] and vault != entry['output']['vaultUuid']:
                continue

            match_fields = [
                entry['output']['uuid'],
                entry['output']['overview']['title']
            ]

            # Note that exactly how 1Password matches on domains in non-trivial cases is neither documented
            # nor obvious, so this may not precisely match the real behavior.
            urls = entry['output']['overview'].get('URLs')
            if urls is not None:
                match_fields += [urlparse(url['u']).netloc for url in urls]

            if key in match_fields:
                return entry['output']

    def _run(self, args, stdin=None, expected_rc=0):
        parser = ArgumentParser()

        command_parser = parser.add_subparsers(dest='command')

        get_parser = command_parser.add_parser('get')
        get_options = ArgumentParser(add_help=False)
        get_options.add_argument('--vault')
        get_type_parser = get_parser.add_subparsers(dest='object_type')
        get_type_parser.add_parser('account', parents=[get_options])
        get_item_parser = get_type_parser.add_parser('item', parents=[get_options])
        get_item_parser.add_argument('item_id')

        args = parser.parse_args(args)

        def mock_exit(output='', error='', rc=0):
            if rc != expected_rc:
                raise OnePassException(error)
            if error != '':
                now = datetime.date.today()
                error = '[LOG] {0} (ERROR) {1}'.format(now.strftime('%Y/%m/%d %H:$M:$S'), error)
            return output, error

        if args.command == 'get':
            if self._mock_logged_out:
                return mock_exit(error='You are not currently signed in. Please run `op signin --help` for instructions', rc=1)

            if self._mock_timed_out:
                return mock_exit(error='401: Authentication required.', rc=1)

            if args.object_type == 'item':
                mock_entry = self._lookup_mock_entry(args.item_id, args.vault)

                if mock_entry is None:
                    return mock_exit(error='Item {0} not found'.format(args.item_id))

                return mock_exit(output=json.dumps(mock_entry))

            if args.object_type == 'account':
                # Since we don't actually ever use this output, don't bother mocking output.
                return mock_exit()

        raise OnePassException('Unsupported command string passed to OnePass mock: {0}'.format(args))


class LoggedOutMockOnePass(MockOnePass):

    _mock_logged_out = True


class TimedOutMockOnePass(MockOnePass):

    _mock_timed_out = True


class TestOnePass(unittest.TestCase):

    def test_onepassword_cli_path(self):
        op = MockOnePass(path='/dev/null')
        self.assertEqual('/dev/null', op.cli_path)

    def test_onepassword_logged_in(self):
        op = MockOnePass()
        try:
            op.assert_logged_in()
        except:
            self.fail()

    def test_onepassword_logged_out(self):
        op = LoggedOutMockOnePass()
        with self.assertRaises(OnePassException):
            op.assert_logged_in()

    def test_onepassword_timed_out(self):
        op = TimedOutMockOnePass()
        with self.assertRaises(OnePassException):
            op.assert_logged_in()

    def test_onepassword_get(self):
        op = MockOnePass()
        query_generator = get_mock_query_generator()
        for dummy, query, field in query_generator:
            self.assertEqual(field['v'], op.get_field(query, field['t']))

    def test_onepassword_get_not_found(self):
        op = MockOnePass()
        self.assertEqual('', op.get_field('a fake query', 'a fake field'))

    def test_onepassword_get_with_vault(self):
        op = MockOnePass()
        entry, query, field = get_one_mock_query()
        for vault_query in [entry['vault_name'], entry['output']['vaultUuid']]:
            self.assertEqual(field['v'], op.get_field(query, field['t'], vault_query))

    def test_onepassword_get_with_wrong_vault(self):
        op = MockOnePass()
        dummy, query, field = get_one_mock_query()
        self.assertEqual('', op.get_field(query, field['t'], 'a fake vault'))


@patch('ansible.plugins.lookup.onepassword.OnePass', MockOnePass)
class TestLookupModule(unittest.TestCase):

    def test_onepassword_plugin_multiple(self):
        lookup_plugin = LookupModule()

        entry = MOCK_ENTRIES[0]
        field = entry['output']['details']['sections'][0]['fields'][0]

        self.assertEqual(
            [field['v']] * len(entry['queries']),
            lookup_plugin.run(entry['queries'], field=field['t'])
        )

    def test_onepassword_plugin_default_field(self):
        lookup_plugin = LookupModule()

        dummy, query, field = get_one_mock_query('password')
        self.assertEqual([field['v']], lookup_plugin.run([query]))
