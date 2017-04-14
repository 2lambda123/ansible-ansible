#!/usr/bin/python
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


DOCUMENTATION = '''
---
module: os_user
short_description: Manage OpenStack Identity Users
extends_documentation_fragment: openstack
author: David Shrewsbury
version_added: "2.0"
description:
    - Manage OpenStack Identity users. Users can be created,
      updated or deleted using this module. A user will be updated
      if I(name) matches an existing user and I(state) is present.
      The value for I(name) cannot be updated without deleting and
      re-creating the user.
options:
   name:
     description:
        - Username for the user
     required: true
   password:
     description:
        - Password for the user
     required: false
     default: None
   update_password:
     required: false
     default: always
     choices: ['always', 'on_create']
     version_added: "2.3"
     description:
        - C(always) will attempt to update password if they differ.  C(on_create) will only
          set the password for newly created users.
   email:
     description:
        - Email address for the user
     required: false
     default: None
   description:
     description:
        - Description about the user
     version_added: "2.4"
   default_project:
     description:
        - Project name or ID that the user should be associated with by default
     required: false
     default: None
   domain:
     description:
        - Domain to create the user in if the cloud supports domains
     required: false
     default: None
   enabled:
     description:
        - Is the user enabled
     required: false
     default: True
   state:
     description:
       - Should the resource be present or absent.
     choices: [present, absent]
     default: present
   availability_zone:
     description:
       - Ignored. Present for backwards compatibility
     required: false
requirements:
    - "python >= 2.6"
    - "shade"
'''

EXAMPLES = '''
# Create a user
- os_user:
    cloud: mycloud
    state: present
    name: demouser
    password: secret
    email: demo@example.com
    domain: default
    default_project: demo

# Delete a user
- os_user:
    cloud: mycloud
    state: absent
    name: demouser

# Create a user but don't update password if user exists
- os_user:
    cloud: mycloud
    state: present
    name: demouser
    password: secret
    update_password: on_create
    email: demo@example.com
    domain: default
    default_project: demo
'''


RETURN = '''
user:
    description: Dictionary describing the user.
    returned: On success when I(state) is 'present'
    type: complex
    contains:
        default_project_id:
            description: User default project ID. Only present with Keystone >= v3.
            type: string
            sample: "4427115787be45f08f0ec22a03bfc735"
        domain_id:
            description: User domain ID. Only present with Keystone >= v3.
            type: string
            sample: "default"
        email:
            description: User email address
            type: string
            sample: "demo@example.com"
        id:
            description: User ID
            type: string
            sample: "f59382db809c43139982ca4189404650"
        name:
            description: User name
            type: string
            sample: "demouser"
'''

try:
    import shade
    from keystoneauth1 import exceptions as ks_exc
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

from distutils.version import StrictVersion

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.openstack import openstack_full_argument_spec, openstack_module_kwargs, openstack_cloud_from_module


def _password_needs_update(username, default_project_id, params_dict, cloud, module):
    if (params_dict['password'] is None or
            params_dict['update_password'] != 'always'):
        return False

    if cloud is None:
        return True

    if default_project_id is None:
        module.warn("Could not find default_project_id for user, which is needed to check if password needs to be changed. Password will be updated.")
        return True

    try:
        if shade.openstack_cloud(username=username,
                                 password=params_dict['password'],
                                 project_id=default_project_id,
                                 auth_url=cloud.auth['auth_url']).keystone_client is not None:
            return False
    except ks_exc.http.Unauthorized:
        # passwords differ
        return True
    except Exception as ex:
        template = "An exception of type {0} occurred. Arguments:\n{1!r}"
        message = template.format(ex.__class__, ex.args)
        module.warn("Could not connect using username, password and project_id to verify password. Password will be updated. %s\n" % message)
        return True

    return True


def _needs_update(params_dict, user):
    for k in params_dict:
        if k not in ('password', 'update_password') and user[k] != params_dict[k]:
            return True

    return False


def _get_domain_id(cloud, domain):
    try:
        # We assume admin is passing domain id
        domain_id = cloud.get_domain(domain)['id']
    except:
        # If we fail, maybe admin is passing a domain name.
        # Note that domains have unique names, just like id.
        try:
            domain_id = cloud.search_domains(filters={'name': domain})[0]['id']
        except:
            # Ok, let's hope the user is non-admin and passing a sane id
            domain_id = domain

    return domain_id


def _get_default_project_id(cloud, default_project, module):
    project = cloud.get_project(default_project)
    if not project:
        module.fail_json(msg='Default project %s is not valid' % default_project)

    return project['id']


def main():
    argument_spec = openstack_full_argument_spec(
        name=dict(required=True),
        password=dict(required=False, default=None, no_log=True),
        email=dict(required=False, default=None),
        default_project=dict(required=False, default=None),
        description=dict(type='str'),
        domain=dict(required=False, default=None),
        enabled=dict(default=True, type='bool'),
        state=dict(default='present', choices=['absent', 'present']),
        update_password=dict(default='always', choices=['always', 'on_create']),
    )

    module_kwargs = openstack_module_kwargs()
    module = AnsibleModule(
        argument_spec,
        **module_kwargs)

    name = module.params['name']
    password = module.params.get('password')
    email = module.params['email']
    default_project = module.params['default_project']
    domain = module.params['domain']
    enabled = module.params['enabled']
    state = module.params['state']
    update_password = module.params['update_password']
    description = module.params['description']

    if description and StrictVersion(shade.__version__) < StrictVersion('1.13.0'):
        module.fail_json(msg="To utilize description, the installed version of the shade library MUST be >=1.13.0")

    shade, cloud = openstack_cloud_from_module(module)
    try:
        user = cloud.get_user(name)

        domain_id = None
        if domain:
            domain_id = _get_domain_id(cloud, domain)

        if state == 'present':
            if update_password in ('always', 'on_create'):
                if not password:
                    msg = "update_password is %s but a password value is missing" % update_password
                    module.fail_json(msg=msg)
            default_project_id = None
            if default_project:
                default_project_id = _get_default_project_id(cloud, default_project, module)

            if user is None:
                if description is not None:
                    user = cloud.create_user(
                        name=name, password=password, email=email,
                        default_project=default_project_id, domain_id=domain_id,
                        enabled=enabled, description=description)
                else:
                    user = cloud.create_user(
                        name=name, password=password, email=email,
                        default_project=default_project_id, domain_id=domain_id,
                        enabled=enabled)
                changed = True
            else:
                params_dict = {'email': email, 'enabled': enabled,
                               'password': password,
                               'update_password': update_password}
                if description is not None:
                    params_dict['description'] = description
                if domain_id is not None:
                    params_dict['domain_id'] = domain_id
                if default_project_id is not None:
                    params_dict['default_project_id'] = default_project_id

                password_needs_update = _password_needs_update(name, user.get('default_project_id'), params_dict, cloud, module)
                if _needs_update(params_dict, user) or password_needs_update:
                    if password_needs_update:
                        if description is not None:
                            user = cloud.update_user(
                                user['id'], password=password, email=email,
                                default_project=default_project_id,
                                domain_id=domain_id, enabled=enabled, description=description)
                        else:
                            user = cloud.update_user(
                                user['id'], password=password, email=email,
                                default_project=default_project_id,
                                domain_id=domain_id, enabled=enabled)
                    else:
                        if description is not None:
                            user = cloud.update_user(
                                user['id'], email=email,
                                default_project=default_project_id,
                                domain_id=domain_id, enabled=enabled, description=description)
                        else:
                            user = cloud.update_user(
                                user['id'], email=email,
                                default_project=default_project_id,
                                domain_id=domain_id, enabled=enabled)
                    changed = True
                else:
                    changed = False
            module.exit_json(changed=changed, user=user)

        elif state == 'absent':
            if user is None:
                changed = False
            else:
                cloud.delete_user(user['id'])
                changed = True
            module.exit_json(changed=changed)

    except shade.OpenStackCloudException as e:
        module.fail_json(msg=str(e), extra_data=e.extra_data)


if __name__ == '__main__':
    main()
