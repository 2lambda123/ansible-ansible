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


from ansible import constants as C
from ansible.parsing.splitter import parse_kv
from ansible.utils.unicode import to_unicode

def combine_vars(a, b):

    if C.DEFAULT_HASH_BEHAVIOUR == "merge":
        return merge_hash(a, b)
    else:
        return dict(a.items() + b.items())

def merge_hash(a, b):
    ''' recursively merges hash b into a
    keys from b take precedence over keys from a '''

    result = {}

    for dicts in a, b:
        # next, iterate over b keys and values
        for k, v in dicts.iteritems():
            # if there's already such key in a
            # and that key contains dict
            if k in result and isinstance(result[k], dict):
                # merge those dicts recursively
                result[k] = merge_hash(a[k], v)
            else:
                # otherwise, just copy a value from b to a
                result[k] = v

    return result

def load_extra_vars(loader, options):
    extra_vars = {}
    for extra_vars_opt in options.extra_vars:
        extra_vars_opt = to_unicode(extra_vars_opt, errors='strict')
        if extra_vars_opt.startswith(u"@"):
            # Argument is a YAML file (JSON is a subset of YAML)
            data = loader.load_from_file(extra_vars_opt[1:])
        elif extra_vars_opt and extra_vars_opt[0] in u'[{':
            # Arguments as YAML
            data = loader.load(extra_vars_opt)
        else:
            # Arguments as Key-value
            data = parse_kv(extra_vars_opt)
        extra_vars = combine_vars(extra_vars, data)
    return extra_vars
