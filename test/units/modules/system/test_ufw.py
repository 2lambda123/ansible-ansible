
from units.compat import unittest
from units.compat.mock import patch
from ansible.module_utils import basic
from ansible.module_utils._text import to_bytes
import ansible.modules.system.ufw as module

import json


# mock ufw messages

ufw_version_35 = """ufw 0.35\nCopyright 2008-2015 Canonical Ltd.\n"""
ufw_status_verbose_with_port_7000 = """Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
7000/tcp                   ALLOW IN    Anywhere
7000/tcp (v6)              ALLOW IN    Anywhere (v6)
"""

user_rules_with_port_7000 = """### tuple ### allow tcp 7000 0.0.0.0/0 any 0.0.0.0/0 in
### tuple ### allow tcp 7000 ::/0 any ::/0 in
"""

user_rules_with_ipv6 = """### tuple ### allow udp 5353 0.0.0.0/0 any 224.0.0.251 in
### tuple ### allow udp 5353 ::/0 any ff02::fb in
"""


# result of
# sudo ufw allow in from ff02::fb port 5353 proto udp
# ufw allow in from 224.0.0.251 port 5353 proto udp
ufw_status_verbose_with_ipv6 = """sudo ufw status verbose
État : actif
Journalisation : on (full)
Par défaut : allow (incoming), allow (outgoing), deny (routed)
Nouveaux profils : skip

Vers                       Action      De
----                       ------      --
5353/udp                   ALLOW IN    224.0.0.251
5353/udp                   ALLOW IN    ff02::fb
"""

skippg_adding_existing_rules = "Skipping adding existing rule\nSkipping adding existing rule (v6)\n"

grep_config_cli = "grep -h '^### tuple' /lib/ufw/user.rules /lib/ufw/user6.rules /etc/ufw/user.rules /etc/ufw/user6.rules "
grep_config_cli += "/var/lib/ufw/user.rules /var/lib/ufw/user6.rules"

dry_mode_cmd_with_port_700 = {
    "ufw status verbose": ufw_status_verbose_with_port_7000,
    "ufw --version": ufw_version_35,
    "ufw --dry-run allow from any to any port 7000 proto tcp": skippg_adding_existing_rules,
    "ufw --dry-run delete allow from any to any port 7000 proto tcp": "",
    "ufw --dry-run delete allow from any to any port 7001 proto tcp": user_rules_with_port_7000,
    grep_config_cli: user_rules_with_port_7000
}

dry_mode_cmd_with_ipv6 = {
    "ufw status verbose": ufw_status_verbose_with_ipv6,
    "ufw --version": ufw_version_35,
    # CONTENT of the command sudo ufw --dry-run delete allow in from ff02::fb port 5353 proto udp | grep -E "^### tupple"
    "ufw --dry-run delete allow from ff02::fb to any port 5353 proto udp": "### tuple ### allow udp any ::/0 5353 ff02::fb in",
    grep_config_cli: user_rules_with_ipv6,
    "ufw --dry-run allow from ff02::fb to any port 5353 proto udp": skippg_adding_existing_rules,
    "ufw --dry-run allow from 224.0.0.252 to any port 5353 proto udp": """### tuple ### allow udp 5353 0.0.0.0/0 any 224.0.0.251 in
### tuple ### allow udp 5353 0.0.0.0/0 any 224.0.0.252 in
"""

}


def set_module_args(args):
    args = json.dumps({'ANSIBLE_MODULE_ARGS': args})
    """prepare arguments so that they will be picked up during module creation"""
    basic._ANSIBLE_ARGS = to_bytes(args)


class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def do_nothing_func_ipv6(*args, **kwarg):
    return 0, dry_mode_cmd_with_ipv6[args[0]], ""


def do_nothing_func_port_7000(*args, **kwarg):
    return 0, dry_mode_cmd_with_port_700[args[0]], ""


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


def get_bin_path(self, arg, required=False):
    """Mock AnsibleModule.get_bin_path"""
    return arg


class TestUFW(unittest.TestCase):

    def setUp(self):
        self.mock_module_helper = patch.multiple(basic.AnsibleModule,
                                                 exit_json=exit_json,
                                                 fail_json=fail_json,
                                                 get_bin_path=get_bin_path)
        self.mock_module_helper.start()
        self.addCleanup(self.mock_module_helper.stop)

    def test_filter_line_that_contains_ipv4(self):
        self.assertEqual(module.filter_line_that_contains_ipv4(user_rules_with_ipv6).strip(),
                         "### tuple ### allow udp 5353 0.0.0.0/0 any 224.0.0.251 in")

    def test_filter_line_that_contains_ipv6(self):
        self.assertEqual(module.filter_line_that_contains_ipv6(user_rules_with_ipv6).strip(),
                         "### tuple ### allow udp 5353 ::/0 any ff02::fb in")

    def test_check_mode_add_rules(self):
        set_module_args({
            'rule': 'allow',
            'proto': 'tcp',
            'port': '7000',
            '_ansible_check_mode': True
        })
        result = self.__getResult(do_nothing_func_port_7000)
        self.assertFalse(result.exception.args[0]['changed'])

    def test_check_mode_delete_existing_rules(self):

        set_module_args({
            'rule': 'allow',
            'proto': 'tcp',
            'port': '7000',
            'delete': 'yes',
            '_ansible_check_mode': True,
        })

        self.assertTrue(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_check_mode_delete_not_existing_rules(self):

        set_module_args({
            'rule': 'allow',
            'proto': 'tcp',
            'port': '7001',
            'delete': 'yes',
            '_ansible_check_mode': True,
        })

        self.assertTrue(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_enable_mode(self):
        set_module_args({
            'state': 'enabled',
            '_ansible_check_mode': True
        })

        self.assertFalse(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_disable_mode(self):
        set_module_args({
            'state': 'disabled',
            '_ansible_check_mode': True
        })

        self.assertTrue(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_logging_off(self):
        set_module_args({
            'logging': 'off',
            '_ansible_check_mode': True
        })

        self.assertTrue(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_logging_on(self):
        set_module_args({
            'logging': 'on',
            '_ansible_check_mode': True
        })

        self.assertFalse(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_default_changed(self):
        set_module_args({
            'default': 'allow',
            "direction": "incoming",
            '_ansible_check_mode': True
        })
        self.assertTrue(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_default_not_changed(self):
        set_module_args({
            'default': 'deny',
            "direction": "incoming",
            '_ansible_check_mode': True
        })
        self.assertFalse(self.__getResult(do_nothing_func_port_7000).exception.args[0]['changed'])

    def test_ipv6_remove(self):
        set_module_args({
            'rule': 'allow',
            'proto': 'udp',
            'port': '5353',
            'from': 'ff02::fb',
            'delete': 'yes',
            '_ansible_check_mode': True,
        })
        self.assertTrue(self.__getResult(do_nothing_func_ipv6).exception.args[0]['changed'])

    def test_ipv6_add_existing(self):
        set_module_args({
            'rule': 'allow',
            'proto': 'udp',
            'port': '5353',
            'from': 'ff02::fb',
            '_ansible_check_mode': True,
        })
        self.assertFalse(self.__getResult(do_nothing_func_ipv6).exception.args[0]['changed'])

    def test_ipv6_add(self):
        set_module_args({
            'rule': 'allow',
            'proto': 'udp',
            'port': '5353',
            'from': '224.0.0.252',
            '_ansible_check_mode': True,
        })
        self.assertTrue(self.__getResult(do_nothing_func_ipv6).exception.args[0]['changed'])

    def __getResult(self, cmd_fun):
        with patch.object(basic.AnsibleModule, 'run_command') as mock_run_command:
            mock_run_command.side_effect = cmd_fun
            with self.assertRaises(AnsibleExitJson) as result:
                module.main()
        return result
