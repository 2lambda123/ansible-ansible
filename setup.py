#!/usr/bin/env python

import os
import sys
from glob import glob

sys.path.insert(0, os.path.abspath('lib'))
from ansible import __version__, __author__
try:
   from setuptools import setup
except ImportError:
   from distutils.core import setup

# find library modules
from ansible.constants import DIST_MODULE_PATH
data_files = [ (DIST_MODULE_PATH, glob('./library/*')) ]

print "DATA FILES=%s" % data_files

setup(name='ansible',
      version=__version__,
      description='Minimal SSH command and control',
      author=__author__,
      author_email='michael.dehaan@gmail.com',
      url='http://ansible.github.com/',
      license='GPLv3',
      install_requires=['paramiko', 'jinja2', "PyYAML"],
      package_dir={ 'ansible': 'lib/ansible' },
      packages=[
         'ansible',
         'ansible.scripts',
         'ansible.utils',
         'ansible.inventory',
         'ansible.inventory.vars_plugins',
         'ansible.playbook',
         'ansible.runner',
         'ansible.runner.action_plugins',
         'ansible.runner.lookup_plugins',
         'ansible.runner.connection_plugins',
         'ansible.runner.action_plugins',
         'ansible.runner.filter_plugins',
         'ansible.callback_plugins',
      ],
      entry_points = dict(console_scripts=[
         'ansible=ansible.scripts:ansible',
         'ansible-playbook=ansible.scripts:ansible_playbook',
         'ansible-pull=ansible.scripts:ansible_pull',
         'ansible-doc=ansible.scripts:ansible_doc'
      ]),
      scripts=[
         'bin/ansible',
         'bin/ansible-playbook',
         'bin/ansible-pull',
         'bin/ansible-doc'
      ],
      data_files=data_files
)
