#!/usr/bin/python

# (c) 2017, Tal Shafir

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
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# python 3 compability
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: os_tempest_parse_results
short_description: parse subunit file
description:
    - Parses subunit file to the format the user chose, using subunit's and ostestr's filters

version_added: "2.8"

author: "Tal Shafir , @TalShafir"
requirements: ["os-testr","python-subunit", "junitxml"]
options:
  src:
    description:
      path to the subunit file
    required: True
  dest:
    description:
      path to the parsed results file this module will generated
    required: False
    default: ~/test-results
  output_format:
    description:
       format of the parsed results file this module will generated
    type: bool
    required: False
    default: html
    choices: [xml, html]
  force:
    description:
      override output file if already exists
    required: False
    default: False
notes:
  - For more information about os-testr, U(https://docs.openstack.org/developer/os-testr)
  - For more information about python-subunit, U(https://pypi.python.org/pypi/python-subunit)
  - For more information about junitxml, U(https://pypi.python.org/pypi/junitxml)
'''
EXAMPLES = '''
# Parse subunit file to the default path in the default format
- os_tempest_parse_results:
  src: /path/to/subunit_file

# Parse subunit file to custom path in the default format
- os_tempest_parse_results:
  src: /path/to/subunit_file
  dest: /path/to/parsed_output

# Parse subunit file to the default path in another supported format(mentioned in the description of I(output_format))
- os_tempest_parse_results:
  src: /path/to/subunit_file
  output_format: FORMAT
'''
RETURN = '''
dest:
  description: destination file path
  returned: success
  type: string
  sample: "/path/to/file"
exception:
  description: python exception message
  returned: fail
  type: string
'''
from ansible.module_utils.basic import AnsibleModule
import os

try:
    from os_testr.subunit2html import HtmlOutput
    from os_testr.subunit2html import FileAccumulator
    import testtools

    SUPPORT_HTML = True
except ImportError:
    SUPPORT_HTML = False

try:
    import subunit.filters
    from testtools import StreamToExtendedDecorator
    from junitxml import JUnitXmlResult

    SUPPORT_XML = True
except ImportError as e:
    SUPPORT_XML = False

# imports for the code copied from ansible.utils.path
from errno import EEXIST
from ansible.module_utils._text import to_bytes
from ansible.module_utils._text import to_native


def main():
    ansible_module = AnsibleModule(argument_spec=dict(
        src=dict(type="path", required=True),
        dest=dict(type="path", required=False, default="~/test_results"),
        output_format=dict(type="str",
                           required=False,
                           default="html",
                           choices=["xml", "html"]),
        force=dict(type="bool", required=False, default=False),
    ))

    src_path = ansible_module.params['src']

    # test if the src file is valid and that all the required packages are available
    if not os.path.isfile(src_path):
        ansible_module.fail_json(msg="the subunit file is not valid", subunit=src_path)
    if ansible_module.params['output_format'] == 'html' and not SUPPORT_HTML:
        ansible_module.fail_json(msg="Couldn't import ostestr's html filter")
    if ansible_module.params['output_format'] == 'xml' and not SUPPORT_XML:
        ansible_module.fail_json(msg="Couldn't import subunit or junitxml")

    if ansible_module.params['dest']:
        dest_path = ansible_module.params['dest']
        if os.path.isdir(dest_path):
            dest_path = os.path.join(dest_path, 'test-results.' + ansible_module.params['output_format'])
    else:
        dest_path = '~/test-results.' + ansible_module.params['output_format']

    if os.path.isfile(dest_path) and not ansible_module.params['force']:
        ansible_module.exit_json(msg="the output file already exists", changed=False, dest=dest_path)

    # create output path if doesn't exists
    try:
        prepare_path(dest_path)
    except Exception as error:
        ansible_module.fail_json(msg=str(error))

    if ansible_module.params['output_format'] == 'html':
        # use subunit2html's main function
        try:
            parse_subunit_to_html(src_path, dest_path)
            ansible_module.exit_json(msg="html file was successfully created", dest=dest_path, changed=True)
        except Exception as exception:
            ansible_module.fail_json(msg="Failed to parse subunit to html", exception=str(exception))

    elif ansible_module.params['output_format'] == 'xml':
        # use subunit2junitxml's main function
        try:
            parse_subunit_to_xml(src_path, dest_path)
            ansible_module.exit_json(msg="xml file was successfully created", dest=dest_path, changed=True)
        except Exception as e:
            ansible_module.fail_json(msg="Failed to parse to xml", exception=str(e))


def parse_subunit_to_xml(subunit_file, xml_file):
    """Parse subunit file to XML file."""

    subunit.filters.filter_by_result(
        lambda output: StreamToExtendedDecorator(JUnitXmlResult(output)),
        xml_file, False, False, protocol_version=2,
        passthrough_subunit=True,
        input_stream=open(subunit_file))


def parse_subunit_to_html(subunit_file, html_file='results.html'):
    """Parse subunit file to HTML file."""

    html_result = HtmlOutput(html_file)
    stream = open(subunit_file, 'rb')

    # Feed the subunit stream through both a V1 and V2 parser.
    # Depends on having the v2 capable libraries installed.
    # First V2.

    suite = subunit.ByteStreamToStreamResult(stream, non_subunit_name="")
    # The HTML output code is in legacy mode.
    result = testtools.StreamToExtendedDecorator(html_result)
    # Divert non-test output
    accumulator = FileAccumulator()
    result = testtools.StreamResultRouter(result)
    result.add_rule(accumulator, 'test_id', test_id=None)
    result.startTestRun()
    suite.run(result)
    # Now reprocess any found stdout content as V1 subunit
    for bytes_io in accumulator.route_codes.values():
        bytes_io.seek(0)
        suite = subunit.ProtocolTestCase(bytes_io)
        suite.run(html_result)
    result.stopTestRun()


def prepare_path(file_path):
    """Creates the path to the dir that contains the file if it doesn't exists"""

    dir_name = os.path.dirname(file_path)
    if not os.path.isdir(dir_name):
        makedirs_safe(dir_name)


# copied from ansible.utils.path
def makedirs_safe(path, mode=None):
    """Safe way to create dirs in muliprocess/thread environments.

    :arg path: A byte or text string representing a directory to be created
    :kwarg mode: If given, the mode to set the directory to
    :raises Exception: If the directory cannot be created and does not already exists.
    :raises UnicodeDecodeError: if the path is not decodable in the utf-8 encoding.
    """

    rpath = path
    b_rpath = to_bytes(rpath)
    if not os.path.exists(b_rpath):
        try:
            if mode:
                os.makedirs(b_rpath, mode)
            else:
                os.makedirs(b_rpath)
        except OSError as e:
            if e.errno != EEXIST:
                raise Exception("Unable to create local directories(%s): %s" % (to_native(rpath), to_native(e)))


if __name__ == '__main__':
    main()
