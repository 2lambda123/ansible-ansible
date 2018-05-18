#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: netconf_get
version_added: "2.6"
author:
    - "Ganesh Nalawade (@ganeshrn)"
    - "Sven Wisotzky (@wisotzky)"
short_description: Fetch configuration/state data from NETCONF enabled network devices.
description:
    - NETCONF is a network management protocol developed and standardized by
      the IETF. It is documented in RFC 6241.
    - This module allows the user to fetch configuration and state data from NETCONF
      enabled network devices.
options:
  source:
    description:
      - This argument specifies the datastore from which configuration data should be fetched.
        Valid values are I(running), I(candidate) and I(startup). If the C(source) value is not
        set both configuration and state information are returned in response from running datastore.
    choices: ['running', 'candidate', 'startup']
  filter:
    description:
      - This argument specifies the XML string which acts as a filter to restrict the portions of
        the data to be are retrieved from the remote device. If this option is not specified entire
        configuration or state data is returned in result depending on the value of C(source)
        option. The C(filter) value can be either XML string or XPath, if the filter is in
        XPath format the NETCONF server running on remote host should support xpath capability
        else it will result in an error.
  display:
    description:
      - Encoding scheme to use when serializing output from the device. The option I(json) will
        serialize the output as JSON data. If the option value is I(json) it requires jxmlease
        to be installed on control node. The option I(pretty) is similar to received XML response
        but is using human readable format (spaces, new lines). The option value I(xml) is similar
        to received XML response but removes all XML namespaces.
    choices: ['json', 'pretty', 'xml']
  lock:
    description:
      - Instructs the module to explicitly lock the datastore specified as C(source) before fetching
        configuration and/or state information from remote host. If the value is I(never) in that case
        the C(source) datastore is never locked, if the value is I(if-supported) the C(source) datastore
        is locked only if the Netconf server running on remote host supports locking of that datastore,
        if the lock on C(source) datastore is not supported module will report appropriate error before
        executing lock. If the value is I(always) the lock operation on C(source) datastore will always
        be executed irrespective if the remote host supports it or not, if it doesn't the module with
        fail will the execption message received from remote host and might vary based on the platform.
    default: 'never'
    choices: ['never', 'always', 'if-supported']
requirements:
  - ncclient (>=v0.5.2)
  - jxmlease

notes:
  - This module requires the NETCONF system service be enabled on
    the remote device being managed.
  - This module supports the use of connection=netconf
"""

EXAMPLES = """
- name: Get running configuration and state data
  netconf_get:

- name: Get configuration and state data from startup datastore
  netconf_get:
    source: startup

- name: Get system configuration data from running datastore state (junos)
  netconf_get:
    source: running
    filter: <configuration><system></system></configuration>

- name: Get configuration and state data in JSON format
  netconf_get:
    display: json

- name: get schema list using subtree w/ namespaces
  netconf_get:
    format: json
    filter: <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"><schemas><schema/></schemas></netconf-state>
    lock: False

- name: get schema list using xpath
  netconf_get:
    format: json
    filter: /netconf-state/schemas/schema

- name: get interface confiugration with filter (iosxr)
  netconf_get:
    filter: <interface-configurations xmlns="http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"></interface-configurations>

- name: Get system configuration data from running datastore state (sros)
  netconf_get:
    source: running
    filter: <state xmlns="urn:nokia.com:sros:ns:yang:sr:conf"/>
    lock: True

- name: Get state data (sros)
  netconf_get:
    filter: <state xmlns="urn:nokia.com:sros:ns:yang:sr:state"/>
"""

RETURN = """
stdout:
  description: The raw XML string containing configuration or state data
               received from the underlying ncclient library.
  returned: always apart from low-level errors (such as action plugin)
  type: string
  sample: '...'
stdout_lines:
  description: The value of stdout split into a list
  returned: always apart from low-level errors (such as action plugin)
  type: list
  sample: ['...', '...']
output:
  description: Based on the value of display option will return either the set of
               transformed XML to JSON format from the RPC response with type dict
               or pretty XML string response (human-readable) or response with
               namespace removed from XML string.
  returned: when the display format is selected as JSON it is returned as dict type, if the
            display format is xml or pretty pretty it is retured as a string apart from low-level
            errors (such as action plugin).
  type: complex
  contains:
    formatted_output:
      - Contains formatted response received from remote host as per the value in display format.
"""
import sys

try:
    from lxml.etree import Element, SubElement, tostring, fromstring, XMLSyntaxError
except ImportError:
    from xml.etree.ElementTree import Element, SubElement, tostring, fromstring
    if sys.version_info < (2, 7):
        from xml.parsers.expat import ExpatError as XMLSyntaxError
    else:
        from xml.etree.ElementTree import ParseError as XMLSyntaxError

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.netconf.netconf import get_capabilities, locked_config, get_config, get
from ansible.module_utils.network.common.netconf import remove_namespaces

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False


def get_filter_type(filter):
    if not filter:
        return None
    else:
        try:
            fromstring(filter)
            return 'subtree'
        except XMLSyntaxError:
            return 'xpath'


def main():
    """entry point for module execution
    """
    argument_spec = dict(
        source=dict(choices=['running', 'candidate', 'startup']),
        filter=dict(),
        display=dict(choices=['json', 'pretty', 'xml']),
        lock=dict(default='never', choices=['never', 'always', 'if-supported'])
    )

    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    capabilities = get_capabilities(module)
    operations = capabilities['device_operations']

    source = module.params['source']
    filter = module.params['filter']
    filter_type = get_filter_type(filter)
    lock = module.params['lock']
    display = module.params['display']

    if source == 'candidate' and not operations.get('supports_commit', False):
        module.fail_json(msg='candidate source is not supported on this device')

    if source == 'startup' and not operations.get('supports_startup', False):
        module.fail_json(msg='startup source is not supported on this device')

    if filter_type == 'xpath' and not operations.get('supports_xpath', False):
        module.fail_json(msg="filter value '%s' of type xpath is not supported on this device" % filter)

    execute_lock = True if lock in ('always', 'if-supported') else False

    if lock == 'always' and not operations.get('supports_lock', False):
        module.fail_json(msg='lock operation is not supported on this device')

    if execute_lock:
        if source is None:
            # if source is None, in that case operation is 'get' and `get` supports
            # fetching data only from running datastore
            if 'running' not in operations.get('lock_datastore', []):
                # lock is not supported, don't execute lock operation
                if lock == 'if-supported':
                    execute_lock = False
                else:
                    module.warn("lock operation on 'running' source is not supported on this device")
        else:
            if source not in operations.get('lock_datastore', []):
                if lock == 'if-supported':
                    # lock is not supported, don't execute lock operation
                    execute_lock = False
                else:
                    module.warn("lock operation on '%s' source is not supported on this device" % source)

    if display == 'json' and not HAS_JXMLEASE:
        module.fail_json(msg='jxmlease is required to display response in json format'
                             'but does not appear to be installed. '
                             'It can be installed using `pip install jxmlease`')

    filter_spec = (filter_type, filter) if filter_type else None

    if source is not None:
        response = get_config(module, source, filter_spec, execute_lock)
    else:
        response = get(module, filter_spec, execute_lock)

    xml_resp = tostring(response)
    output = None

    if display == 'xml':
        output = remove_namespaces(xml_resp)
    elif display == 'json':
        try:
            output = jxmlease.parse(xml_resp)
        except:
            raise ValueError(xml_resp)
    elif display == 'pretty':
        output = tostring(response, pretty_print=True)

    result = {
        'stdout': xml_resp,
        'output': output
    }

    module.exit_json(**result)

if __name__ == '__main__':
    main()
