#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import os
import re
import tempfile
import subprocess


def main():
    ignore_files = frozenset((
        '*/.git_keep',
        '*/galaxy/data/default/role/*/main.yml.j2',
        '*/galaxy/data/default/role/*/test.yml.j2',
        '*/galaxy/data/default/collection/plugins/README.md.j2',
    ))

    non_py_files = []
    for root, _dummy, files in os.walk('lib/ansible/'):
        for filename in files:
            path = os.path.join(root, filename)
            if os.path.splitext(path)[-1] not in ('.py', '.pyc', '.pyo'):
                add = True
                for ignore in ignore_files:
                    if fnmatch.fnmatch(path, ignore):
                        add = False
                if add:
                    non_py_files.append(path[12:])

    with tempfile.TemporaryDirectory() as tmp_dir:
        stdout, _dummy = subprocess.Popen(
            ['python', 'setup.py', 'install', '--root=%s' % tmp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        ).communicate()
        match = re.search('^creating (%s/.*?/(?:site|dist)-packages/ansible)$' % tmp_dir, stdout, flags=re.M)

        for filename in non_py_files:
            path = os.path.join(match.group(1), filename)
            if not os.path.exists(path):
                print('lib/ansible/%s: File not installed' % filename)


if __name__ == '__main__':
    main()
