# (c) 2013, Julien Phalip <jphalip@gmail.com>
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

import shlex
from ansible import utils, errors

try:
    import keyring
    KEYRING_INSTALLED = True
except ImportError:
    KEYRING_INSTALLED = False


class LookupModule(object):
    """
    Looks up a password in the local system's keychain based on the given
    service and username. Requires the 'keyring' module. Example:

        {{ lookup('keychain', 'service="My Service" username="johndoe"') }}
    """

    def __init__(self, basedir=None, **kwargs):
        self.basedir = basedir

    def run(self, terms, inject=None, **kwargs):
        if not KEYRING_INSTALLED:
            raise errors.AnsibleError("Can't LOOKUP(keychain): module keyring is not installed")
        terms = utils.listify_lookup_plugin_terms(terms, self.basedir, inject)
        result = []
        for term in terms:
            tokens = shlex.split(term.encode('utf-8'))
            username = None
            service = None
            # Parse the service and username arguments
            for token in tokens:
                token = token.decode('utf-8')
                if token.find("=") == -1:
                    raise errors.AnsibleError("LOOKUP(keychain) failed to parse: %s" % term)
                key, value = token.split("=", 1)
                if key == 'service':
                    service = value
                elif key == 'username':
                    username = value
            if service is None or username is None:
                raise errors.AnsibleError("LOOKUP(keychain) requires 2 arguments: service and username")
            # Looks up the password from the keychain
            password = keyring.get_password(service, username)
            result.append(password)
        return result