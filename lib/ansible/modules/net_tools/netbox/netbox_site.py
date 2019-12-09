#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# Copyright: (c) 2019, Alexander Stauch (@BlackestDawn) <blacke4dawn@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {"metadata_version": "1.1",
                    "status": ["preview"],
                    "supported_by": "community"}

DOCUMENTATION = r"""
---
module: netbox_site
short_description: Creates or removes sites from Netbox
description:
  - Creates or removes sites from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
  - Alexander Stauch (@BlackestDawn)
requirements:
  - pynetbox
version_added: "2.8"
options:
  netbox_url:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
    type: str
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
    type: str
  data:
    description:
      - Defines the site configuration
    suboptions:
      name:
        description:
          - Name of the site to be created
        required: true
        type: str
      status:
        description:
          - Status of the site
        choices:
          - Active
          - Planned
          - Retired
        type: str
      region:
        description:
          - The region that the site should be associated with
        type: str
      tenant:
        description:
          - The tenant the site will be assigned to
        type: str
      facility:
        description:
          - Data center provider or facility, ex. Equinix NY7
        type: str
      asn:
        description:
          - The ASN associated with the site
        type: int
      time_zone:
        description:
          - Timezone associated with the site, ex. America/Denver
        type: str
      description:
        description:
          - The description of the prefix
        type: str
      physical_address:
        description:
          - Physical address of site
        type: str
      shipping_address:
        description:
          - Shipping address of site
        type: str
      latitude:
        description:
          - Latitude in decimal format
        type: int
      longitude:
        description:
          - Longitude in decimal format
        type: int
      contact_name:
        description:
          - Name of contact for site
        type: str
      contact_phone:
        description:
          - Contact phone number for site
        type: str
      contact_email:
        description:
          - Contact email for site
        type: str
      comments:
        description:
          - Comments for the site. This can be markdown syntax
        type: str
      tags:
        description:
          - Any tags that the prefix may need to be associated with
        type: list
      custom_fields:
        description:
          - must exist in Netbox
        type: dict
    required: true
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
    type: str
  validate_certs:
    description:
      - |
        If C(no), SSL certificates will not be validated.
        This should only be used on personally controlled sites using self-signed certificates.
    default: "yes"
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox site module"
  connection: local
  hosts: localhost
  gather_facts: False
  tasks:
    - name: Create site within Netbox with only required information
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - Colorado
        state: present

    - name: Delete site within netbox
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - Colorado
        state: absent

    - name: Create site with all parameters
      netbox_site:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          name: Test - California
          status: Planned
          region: Test Region
          tenant: Test Tenant
          facility: EquinoxCA7
          asn: 65001
          time_zone: America/Los Angeles
          description: This is a test description
          physical_address: Hollywood, CA, 90210
          shipping_address: Hollywood, CA, 90210
          latitude: 10.100000
          longitude: 12.200000
          contact_name: Jenny
          contact_phone: 867-5309
          contact_email: jenny@changednumber.com
          comments: ### Placeholder
        state: present
"""

RETURN = r"""
site:
  description: Serialized object as created or already existent within Netbox
  returned: on creation
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
"""

import json
import traceback

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.net_tools.netbox.netbox_utils import *
from ansible.module_utils.compat import ipaddress
from ansible.module_utils._text import to_text


PYNETBOX_IMP_ERR = None
try:
    import pynetbox
    HAS_PYNETBOX = True
except ImportError:
    PYNETBOX_IMP_ERR = traceback.format_exc()
    HAS_PYNETBOX = False

class PyNetboxSite(PyNetboxBase):
    def __init__(self, module):
        """Constructor"""
        super(PyNetboxSite, self).__init__(module)
        self._set_endpoint('sites')
        # Main parameters for status messages and return data
        self.param_usage = {
            'type': "site",
            'success': "name",
            'fail': "name",
            'rname': "site",
            'search': "slug"
        }

    def _check_and_adapt_data(self):
        """Overridden parent method"""
        data = self._find_ids()
        if data.get("status"):
            data["status"] = SITE_STATUS.get(data["status"].lower())
        if "-" in data["name"]:
            site_slug = data["name"].replace(" ", "").lower()
        elif " " in data["name"]:
            site_slug = data["name"].replace(" ", "-").lower()
        else:
            site_slug = data["name"].lower()
        data["slug"] = site_slug
        self.normalized_data = data

def main():
    """
    Main entry point for module execution
    """
    argument_spec = netbox_argument_spec()
    argument_spec.update(dict(
        state=dict(required=False, default="present", choices=["present", "absent"])
    ))

    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    pynb = PyNetboxSite(module)

    try:
        pynb.run_module()
    except pynetbox.RequestError as e:
        return module.fail_json(msg=json.loads(e.error))
    except ValueError as e:
        return module.fail_json(msg=str(e))
    except AttributeError as e:
        return module.fail_json(msg=str(e))

if __name__ == "__main__":
    main()
