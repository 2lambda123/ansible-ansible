# (c) 2020 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
    lookup: unvault
    author: ansible core team
    version_added: "2.10"
    short_description: read vaulted file(s) contents
    description:
        - This lookup returns the contents from vaulted (or not) file(s) on the Ansible controller's file system.
    options:
      _terms:
        description: path(s) of files to read
        required: True
    notes:
      - This lookup does not understand 'globbing' nor shell environment variables.
"""

EXAMPLES = """
- debug: msg="the value of foo.txt is {{lookup('unvault', '/etc/foo.txt')|to_string }}"
"""

RETURN = """
  _raw:
    description:
      - content of file(s) as bytes
"""

from ansible.errors import AnsibleParserError
from ansible.plugins.lookup import LookupBase
from ansible.module_utils._text import to_text
from ansible.utils.display import Display

display = Display()


class LookupModule(LookupBase):

    def run(self, terms, variables=None, **kwargs):

        self.set_options(direct=kwargs)

        ret = []

        for term in terms:
            display.debug("Unvault lookup term: %s" % term)

            # Find the file in the expected search path
            lookupfile = self.find_file_in_search_path(variables, 'files', term)
            display.vvvv(u"Unvault lookup found %s" % lookupfile)
            if lookupfile:
                actual_file = self._loader.get_real_file(lookupfile, decrypt=True)
                with open(actual_file, 'rb') as f:
                    b_contents = f.read()
                ret.append(b_contents)
            else:
                raise AnsibleParserError('Unable to find file matching "%s" ' % term)

        return ret
