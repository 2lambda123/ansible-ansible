# (c) 2014, James Tanner <tanner.jc@gmail.com>
# (c) 2014, James Cammarata, <jcammarata@ansible.com>
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

from multiprocessing import Event, Pipe, Process
import os
import stat
import tempfile
import time

import pytest

from ansible.compat.tests import unittest
from ansible.compat.tests.mock import patch

from ansible import errors
from ansible.parsing import vault
from ansible.parsing.vault import VaultLib, VaultEditor, match_encrypt_secret
from ansible.parsing.vault import VaultEditorLock

from ansible.module_utils._text import to_bytes, to_text

from units.mock.vault_helper import TextVaultSecret

v10_data = """$ANSIBLE_VAULT;1.0;AES
53616c7465645f5fd0026926a2d415a28a2622116273fbc90e377225c12a347e1daf4456d36a77f9
9ad98d59f61d06a4b66718d855f16fb7bdfe54d1ec8aeaa4d06c2dc1fa630ae1846a029877f0eeb1
83c62ffb04c2512995e815de4b4d29ed"""

v11_data = """$ANSIBLE_VAULT;1.1;AES256
62303130653266653331306264616235333735323636616539316433666463323964623162386137
3961616263373033353631316333623566303532663065310a393036623466376263393961326530
64336561613965383835646464623865663966323464653236343638373165343863623638316664
3631633031323837340a396530313963373030343933616133393566366137363761373930663833
3739"""


@pytest.mark.skipif(not vault.HAS_CRYPTOGRAPHY,
                    reason="Skipping cryptography tests because cryptography is not installed")
class TestVaultEditor(unittest.TestCase):

    def setUp(self):
        self._test_dir = None
        self.vault_password = "test-vault-password"
        vault_secret = TextVaultSecret(self.vault_password)
        self.vault_secrets = [('vault_secret', vault_secret),
                              ('default', vault_secret)]

    @property
    def vault_secret(self):
        return match_encrypt_secret(self.vault_secrets)[1]

    def tearDown(self):
        if self._test_dir:
            pass
            # shutil.rmtree(self._test_dir)
        self._test_dir = None

    def _secrets(self, password):
        vault_secret = TextVaultSecret(password)
        vault_secrets = [('default', vault_secret)]
        return vault_secrets

    def test_methods_exist(self):
        v = vault.VaultEditor(None)
        slots = ['create_file',
                 'decrypt_file',
                 'edit_file',
                 'encrypt_file',
                 'rekey_file',
                 'read_data',
                 'write_data']
        for slot in slots:
            assert hasattr(v, slot), "VaultLib is missing the %s method" % slot

    def _create_test_dir(self):
        suffix = '_ansible_unit_test_%s_' % (self.__class__.__name__)
        return tempfile.mkdtemp(suffix=suffix)

    def _create_file(self, test_dir, name, content=None, symlink=False):
        file_path = os.path.join(test_dir, name)
        opened_file = open(file_path, 'wb')
        if content:
            opened_file.write(content)
        opened_file.close()
        return file_path

    def _vault_editor(self, vault_secrets=None):
        if vault_secrets is None:
            vault_secrets = self._secrets(self.vault_password)
        return VaultEditor(VaultLib(vault_secrets))

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_helper_empty_target(self, mock_sp_call):
        self._test_dir = self._create_test_dir()

        src_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        mock_sp_call.side_effect = self._faux_command
        ve = self._vault_editor()

        b_ciphertext = ve._edit_file_helper(src_file_path, self.vault_secret)

        self.assertNotEqual(src_contents, b_ciphertext)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_helper_call_exception(self, mock_sp_call):
        self._test_dir = self._create_test_dir()

        src_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        error_txt = 'calling editor raised an exception'
        mock_sp_call.side_effect = errors.AnsibleError(error_txt)

        ve = self._vault_editor()

        self.assertRaisesRegexp(errors.AnsibleError,
                                error_txt,
                                ve._edit_file_helper,
                                src_file_path,
                                self.vault_secret)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_helper_symlink_target(self, mock_sp_call):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        src_file_link_path = os.path.join(self._test_dir, 'a_link_to_dest_file')

        os.symlink(src_file_path, src_file_link_path)

        mock_sp_call.side_effect = self._faux_command
        ve = self._vault_editor()

        b_ciphertext = ve._edit_file_helper(src_file_link_path, self.vault_secret)

        self.assertNotEqual(src_file_contents, b_ciphertext,
                            'b_ciphertext should be encrypted and not equal to src_contents')

    def _faux_editor(self, editor_args, new_src_contents=None):
        if editor_args[0] == 'shred':
            return

        tmp_path = editor_args[-1]

        # simulate the tmp file being editted
        tmp_file = open(tmp_path, 'wb')
        if new_src_contents:
            tmp_file.write(new_src_contents)
        tmp_file.close()

    def _faux_command(self, tmp_path):
        pass

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_helper_no_change(self, mock_sp_call):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        # editor invocation doesn't change anything
        def faux_editor(editor_args):
            self._faux_editor(editor_args, src_file_contents)

        mock_sp_call.side_effect = faux_editor
        ve = self._vault_editor()

        ve._edit_file_helper(src_file_path, self.vault_secret, existing_data=src_file_contents)

        new_target_file = open(src_file_path, 'rb')
        new_target_file_contents = new_target_file.read()
        self.assertEqual(src_file_contents, new_target_file_contents)

    def _assert_file_is_encrypted(self, vault_editor, src_file_path, src_contents):
        new_src_file = open(src_file_path, 'rb')
        new_src_file_contents = new_src_file.read()

        # TODO: assert that it is encrypted
        self.assertTrue(vault.is_encrypted(new_src_file_contents))

        src_file_plaintext = vault_editor.vault.decrypt(new_src_file_contents)

        # the plaintext should not be encrypted
        self.assertFalse(vault.is_encrypted(src_file_plaintext))

        # and the new plaintext should match the original
        self.assertEqual(src_file_plaintext, src_contents)

    def _assert_file_is_link(self, src_file_link_path, src_file_path):
        self.assertTrue(os.path.islink(src_file_link_path),
                        'The dest path (%s) should be a symlink to (%s) but is not' % (src_file_link_path, src_file_path))

    def test_rekey_file(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()
        ve.encrypt_file(src_file_path, self.vault_secret)

        # FIXME: update to just set self._secrets or just a new vault secret id
        new_password = 'password2:electricbugaloo'
        new_vault_secret = TextVaultSecret(new_password)
        new_vault_secrets = [('default', new_vault_secret)]
        ve.rekey_file(src_file_path, vault.match_encrypt_secret(new_vault_secrets)[1])

        # FIXME: can just update self._secrets here
        new_ve = vault.VaultEditor(VaultLib(new_vault_secrets))
        self._assert_file_is_encrypted(new_ve, src_file_path, src_file_contents)

    def test_rekey_file_no_new_password(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()
        ve.encrypt_file(src_file_path, self.vault_secret)

        self.assertRaisesRegexp(errors.AnsibleError,
                                'The value for the new_password to rekey',
                                ve.rekey_file,
                                src_file_path,
                                None)

    def test_rekey_file_not_encrypted(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()

        new_password = 'password2:electricbugaloo'
        self.assertRaisesRegexp(errors.AnsibleError,
                                'input is not vault encrypted data',
                                ve.rekey_file,
                                src_file_path, new_password)

    def test_plaintext(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()
        ve.encrypt_file(src_file_path, self.vault_secret)

        res = ve.plaintext(src_file_path)
        self.assertEqual(src_file_contents, res)

    def test_plaintext_not_encrypted(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()
        self.assertRaisesRegexp(errors.AnsibleError,
                                'input is not vault encrypted data',
                                ve.plaintext,
                                src_file_path)

    def test_encrypt_file(self):
        self._test_dir = self._create_test_dir()
        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        ve = self._vault_editor()
        ve.encrypt_file(src_file_path, self.vault_secret)

        self._assert_file_is_encrypted(ve, src_file_path, src_file_contents)

    def test_encrypt_file_symlink(self):
        self._test_dir = self._create_test_dir()

        src_file_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_file_contents)

        src_file_link_path = os.path.join(self._test_dir, 'a_link_to_dest_file')
        os.symlink(src_file_path, src_file_link_path)

        ve = self._vault_editor()
        ve.encrypt_file(src_file_link_path, self.vault_secret)

        self._assert_file_is_encrypted(ve, src_file_path, src_file_contents)
        self._assert_file_is_encrypted(ve, src_file_link_path, src_file_contents)

        self._assert_file_is_link(src_file_link_path, src_file_path)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_no_vault_id(self, mock_sp_call):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")

        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        new_src_contents = to_bytes("The info is different now.")

        def faux_editor(editor_args):
            self._faux_editor(editor_args, new_src_contents)

        mock_sp_call.side_effect = faux_editor

        ve = self._vault_editor()

        ve.encrypt_file(src_file_path, self.vault_secret)
        ve.edit_file(src_file_path)

        new_src_file = open(src_file_path, 'rb')
        new_src_file_contents = new_src_file.read()

        self.assertTrue(b'$ANSIBLE_VAULT;1.1;AES256' in new_src_file_contents)

        src_file_plaintext = ve.vault.decrypt(new_src_file_contents)
        self.assertEqual(src_file_plaintext, new_src_contents)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_with_vault_id(self, mock_sp_call):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")

        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        new_src_contents = to_bytes("The info is different now.")

        def faux_editor(editor_args):
            self._faux_editor(editor_args, new_src_contents)

        mock_sp_call.side_effect = faux_editor

        ve = self._vault_editor()

        ve.encrypt_file(src_file_path, self.vault_secret,
                        vault_id='vault_secrets')
        ve.edit_file(src_file_path)

        new_src_file = open(src_file_path, 'rb')
        new_src_file_contents = new_src_file.read()

        self.assertTrue(b'$ANSIBLE_VAULT;1.2;AES256;vault_secrets' in new_src_file_contents)

        src_file_plaintext = ve.vault.decrypt(new_src_file_contents)
        self.assertEqual(src_file_plaintext, new_src_contents)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_symlink(self, mock_sp_call):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")

        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        new_src_contents = to_bytes("The info is different now.")

        def faux_editor(editor_args):
            self._faux_editor(editor_args, new_src_contents)

        mock_sp_call.side_effect = faux_editor

        ve = self._vault_editor()

        ve.encrypt_file(src_file_path, self.vault_secret)

        src_file_link_path = os.path.join(self._test_dir, 'a_link_to_dest_file')

        os.symlink(src_file_path, src_file_link_path)

        ve.edit_file(src_file_link_path)

        new_src_file = open(src_file_path, 'rb')
        new_src_file_contents = new_src_file.read()

        src_file_plaintext = ve.vault.decrypt(new_src_file_contents)

        self._assert_file_is_link(src_file_link_path, src_file_path)

        self.assertEqual(src_file_plaintext, new_src_contents)

        # self.assertEqual(src_file_plaintext, new_src_contents,
        #                 'The decrypted plaintext of the editted file is not the expected contents.')

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_file_not_encrypted(self, mock_sp_call):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")

        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        new_src_contents = to_bytes("The info is different now.")

        def faux_editor(editor_args):
            self._faux_editor(editor_args, new_src_contents)

        mock_sp_call.side_effect = faux_editor

        ve = self._vault_editor()
        self.assertRaisesRegexp(errors.AnsibleError,
                                'input is not vault encrypted data',
                                ve.edit_file,
                                src_file_path)

    def test_create_file_exists(self):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        ve = self._vault_editor()
        self.assertRaisesRegexp(errors.AnsibleError,
                                'please use .edit. instead',
                                ve.create_file,
                                src_file_path,
                                self.vault_secret)

    def test_decrypt_file_exception(self):
        self._test_dir = self._create_test_dir()
        src_contents = to_bytes("some info in a file\nyup.")
        src_file_path = self._create_file(self._test_dir, 'src_file', content=src_contents)

        ve = self._vault_editor()
        self.assertRaisesRegexp(errors.AnsibleError,
                                'input is not vault encrypted data',
                                ve.decrypt_file,
                                src_file_path)

    @patch.object(vault.VaultEditor, '_editor_shell_command')
    def test_create_file(self, mock_editor_shell_command):

        def sc_side_effect(filename):
            return ['touch', filename]
        mock_editor_shell_command.side_effect = sc_side_effect

        tmp_file = tempfile.NamedTemporaryFile()
        os.unlink(tmp_file.name)

        _secrets = self._secrets('ansible')
        ve = self._vault_editor(_secrets)
        ve.create_file(tmp_file.name, vault.match_encrypt_secret(_secrets)[1])

        self.assertTrue(os.path.exists(tmp_file.name))

    def test_decrypt_1_0(self):
        # Skip testing decrypting 1.0 files if we don't have access to AES, KDF or Counter.
        v10_file = tempfile.NamedTemporaryFile(delete=False)
        with v10_file as f:
            f.write(to_bytes(v10_data))

        ve = self._vault_editor(self._secrets("ansible"))

        # make sure the password functions for the cipher
        error_hit = False
        try:
            ve.decrypt_file(v10_file.name)
        except errors.AnsibleError:
            error_hit = True
            raise

        # verify decrypted content
        f = open(v10_file.name, "rb")
        fdata = to_text(f.read())
        f.close()

        os.unlink(v10_file.name)

        assert error_hit is False, "error decrypting 1.0 file"
        self.assertEqual(fdata.strip(), "foo")
        assert fdata.strip() == "foo", "incorrect decryption of 1.0 file: %s" % fdata.strip()

    def test_decrypt_1_1(self):
        v11_file = tempfile.NamedTemporaryFile(delete=False)
        with v11_file as f:
            f.write(to_bytes(v11_data))

        ve = self._vault_editor(self._secrets("ansible"))

        # make sure the password functions for the cipher
        error_hit = False
        try:
            ve.decrypt_file(v11_file.name)
        except errors.AnsibleError:
            error_hit = True

        # verify decrypted content
        f = open(v11_file.name, "rb")
        fdata = to_text(f.read())
        f.close()

        os.unlink(v11_file.name)

        assert error_hit is False, "error decrypting 1.1 file"
        assert fdata.strip() == "foo", "incorrect decryption of 1.1 file: %s" % fdata.strip()

    def test_rekey_migration(self):
        v10_file = tempfile.NamedTemporaryFile(delete=False)
        with v10_file as f:
            f.write(to_bytes(v10_data))

        ve = self._vault_editor(self._secrets("ansible"))

        # make sure the password functions for the cipher
        error_hit = False
        new_secrets = self._secrets("ansible2")
        try:
            ve.rekey_file(v10_file.name, vault.match_encrypt_secret(new_secrets)[1])
        except errors.AnsibleError:
            error_hit = True

        # verify decrypted content
        f = open(v10_file.name, "rb")
        fdata = f.read()
        f.close()

        assert error_hit is False, "error rekeying 1.0 file to 1.1"

        # ensure filedata can be decrypted, is 1.1 and is AES256
        vl = VaultLib(new_secrets)
        dec_data = None
        error_hit = False
        try:
            dec_data = vl.decrypt(fdata)
        except errors.AnsibleError:
            error_hit = True

        os.unlink(v10_file.name)

        self.assertIn(b'AES256', fdata, 'AES256 was not found in vault file %s' % to_text(fdata))
        assert error_hit is False, "error decrypting migrated 1.0 file"
        assert dec_data.strip() == b"foo", "incorrect decryption of rekeyed/migrated file: %s" % dec_data

    def test_real_path_dash(self):
        filename = '-'
        ve = self._vault_editor()

        res = ve._real_path(filename)
        self.assertEqual(res, '-')

    def test_real_path_dev_null(self):
        filename = '/dev/null'
        ve = self._vault_editor()

        res = ve._real_path(filename)
        self.assertEqual(res, '/dev/null')

    def test_real_path_symlink(self):
        self._test_dir = self._create_test_dir()
        file_path = self._create_file(self._test_dir, 'test_file', content=b'this is a test file')
        file_link_path = os.path.join(self._test_dir, 'a_link_to_test_file')

        os.symlink(file_path, file_link_path)

        ve = self._vault_editor()

        res = ve._real_path(file_link_path)
        self.assertEqual(res, file_path)

    def _create_test_file(self):
        self._test_dir = self._create_test_dir()
        return self._create_file(self._test_dir, 'test_file', content=b'this is a test file')

    def _test_command_retains_original(self, src_file_path, command_func):
        os.chmod(src_file_path, stat.S_IRUSR | stat.S_IWUSR)
        stat_data = os.stat(src_file_path)
        src_file_mode = stat_data.st_mode
        src_file_owner = [stat_data.st_uid, stat_data.st_gid]
        src_file_inode = stat_data.st_ino

        command_func()

        stat_data = os.stat(src_file_path)
        self.assertEqual(stat_data.st_mode, src_file_mode)
        self.assertEqual([stat_data.st_uid, stat_data.st_gid], src_file_owner)
        self.assertEqual(stat_data.st_ino, src_file_inode)

    def test_encrypt_retains_original(self):
        ve = self._vault_editor()
        ve.exclusive = True
        src_file_path = self._create_test_file()

        def command_func():
            ve.encrypt_file(src_file_path, self.vault_secret)

        self._test_command_retains_original(src_file_path, command_func)

    def test_decrypt_retains_original(self):
        ve = self._vault_editor()
        ve.exclusive = True
        src_file_path = self._create_test_file()
        ve.encrypt_file(src_file_path, self.vault_secret)

        def command_func():
            ve.decrypt_file(src_file_path)

        self._test_command_retains_original(src_file_path, command_func)

    @patch('ansible.parsing.vault.subprocess.call')
    def test_edit_retains_original(self, mock_sp_call):
        ve = self._vault_editor()
        ve.exclusive = True
        src_file_path = self._create_test_file()
        ve.encrypt_file(src_file_path, self.vault_secret)

        def faux_editor(editor_args):
            self._faux_editor(editor_args, b'new file contents')

        mock_sp_call.side_effect = faux_editor

        def command_func():
            ve.edit_file(src_file_path)

        self._test_command_retains_original(src_file_path, command_func)

    def test_rekey_retains_original(self):
        ve = self._vault_editor()
        ve.exclusive = True
        src_file_path = self._create_test_file()
        ve.encrypt_file(src_file_path, self.vault_secret)

        new_secrets = self._secrets("ansible2")

        def command_func():
            ve.rekey_file(src_file_path, vault.match_encrypt_secret(new_secrets)[1])

        self._test_command_retains_original(src_file_path, command_func)

    def test_vault_lock_create(self):
        vault_path = self._create_test_file()
        vl0 = VaultEditorLock(vault_path, readonly=False)
        self.assertEqual(vl0.path, vault_path)
        self.assertFalse(vl0.readonly)
        self.assertFalse(vl0.is_locked)

    def test_vault_lock_acquire(self):
        vault_path = self._create_test_file()
        # test write access failure
        os.chmod(vault_path, stat.S_IRUSR)
        vl = VaultEditorLock(vault_path, readonly=False)
        self.assertRaises(errors.AnsibleError, vl.acquire)
        self.assertFalse(vl.is_locked)
        self.assertTrue(vl.fd is None)
        # test read access failure
        os.chmod(vault_path, 0)
        vl = VaultEditorLock(vault_path, readonly=True)
        self.assertRaises(errors.AnsibleError, vl.acquire)
        self.assertFalse(vl.is_locked)
        self.assertTrue(vl.fd is None)
        # test successful call
        os.chmod(vault_path, stat.S_IRUSR | stat.S_IWUSR)
        vl = VaultEditorLock(vault_path, readonly=False)
        vl.acquire()
        self.assertTrue(vl.is_locked)
        self.assertTrue(vl.fd is not None)
        self.assertFalse(vl.fd.closed)
        vl.__exit__(None, None, None)
        self.assertFalse(vl.is_locked)
        self.assertTrue(vl.fd.closed)
        # test unexpected lock failure

        def fail_lockf(fd, op):
            raise IOError(37)  # unexpected ENOLCK

        vl = VaultEditorLock(vault_path, readonly=False)
        with patch('fcntl.lockf', side_effect=fail_lockf):
            self.assertRaises(errors.AnsibleError, vl.acquire)
            self.assertFalse(vl.is_locked)
            self.assertFalse(vl.fd is None)
            self.assertTrue(vl.fd.closed)

    @staticmethod
    def _subprocess(target, args):
        # it is impossible to test fcntl() locking within the same process
        local, remote = Pipe()
        p = Process(target=target, args=(args + (remote,)))
        p.start()
        p.join()
        return local.recv()

    @staticmethod
    @patch('time.sleep', return_value=None)
    def _vault_reader(vault_path, pipe, time_sleep_mock):
        try:
            with VaultEditorLock(vault_path, readonly=True) as vl:
                pipe.send(vl.is_locked)
        except Exception as exc:
            pipe.send(exc.__class__.__name__)

    def test_vault_lock_use(self):
        vault_path = self._create_test_file()
        # two readers can share a lock
        with VaultEditorLock(vault_path, readonly=True) as vl:
            self.assertTrue(vl.is_locked)
            result = self._subprocess(self._vault_reader, (vault_path,))
            self.assertEqual(result, True)
        self.assertFalse(vl.is_locked)
        # a writer denies access for a concurrent reader
        with VaultEditorLock(vault_path, readonly=False) as vl:
            self.assertTrue(vl.is_locked)
            result = self._subprocess(self._vault_reader, (vault_path,))
            self.assertEqual(result, 'AnsibleVaultError')

    @staticmethod
    def _process_pool(num_workers, target, args):
        # a minimal multiprocessing.Pool replacement that does not require
        # target function to be defined at the module top
        result = []
        for i in range(num_workers):
            local, remote = Pipe(False)
            writer = Process(target=target, args=(args + (remote,)))
            writer.start()
            result.append((writer, local))
        return result

    @staticmethod
    def _vault_writer(vault_path, write_time, retry_time, start_event, pipe):
        time_sleep = time.sleep
        # reduce sleeping time between lock attempts for faster testing
        with patch('time.sleep',
                   side_effect=lambda t: time_sleep(retry_time)):
            try:
                start_event.wait()  # make all writers start at the same time
                with VaultEditorLock(vault_path, readonly=False):
                    pid = os.getpid()
                    with open(vault_path, 'a+') as vault_file:
                        vault_file.write('begin {0}\n'.format(pid))
                        time_sleep(write_time)  # imitate a long write
                        vault_file.write('end {0}\n'.format(pid))
                        pipe.send(True)
            except errors.AnsibleError:
                pipe.send(False)

    def test_vault_lock_single_winner(self):
        vault_path = self._create_test_file()
        start_event = Event()
        # mock time.sleep() so the lock code does not wait until write is done
        writers = self._process_pool(5, self._vault_writer,
                                     (vault_path, 0.1, 0.01, start_event))
        start_event.set()
        [writer.join() for (writer, ignore) in writers]
        results = [pipe.recv() for (ignore, pipe) in writers if pipe.poll(0.1)]
        # there should be one winning writer
        self.assertTrue(any(results))
        results.remove(True)
        # but all others should have been locked and exhaust all retry attempts
        self.assertFalse(any(results))

    def test_vault_lock_cooperation(self):
        vault_path = self._create_test_file()
        open(vault_path, 'w+').close()  # empty the file
        start_event = Event()
        # make the total retry timeout equal to 0.11 * 3 == 0.33
        writers = self._process_pool(5, self._vault_writer,
                                     (vault_path, 0.1, 0.11, start_event))
        start_event.set()
        [writer.join() for (writer, ignore) in writers]
        results = [pipe.recv() for (ignore, pipe) in writers if pipe.poll(0.1)]
        # three writers should have been able to write
        self.assertTrue(len(filter(None, results)) == 3)
        # all writes should be "atomic", i.e "begin"-"end" pairs cannot overlap
        with open(vault_path, 'r') as vault:
            lines = list(vault)
            for index, line in enumerate(lines[1:], 1):
                step, pid = line.split()
                if step == 'end':
                    prev_step, prev_pid = lines[index - 1].split()
                    self.assertEqual(prev_pid, pid)
                    self.assertEqual(prev_step, 'begin')


@pytest.mark.skipif(not vault.HAS_PYCRYPTO,
                    reason="Skipping pycrypto tests because pycrypto is not installed")
class TestVaultEditorPyCrypto(unittest.TestCase):
    def setUp(self):
        self.has_cryptography = vault.HAS_CRYPTOGRAPHY
        vault.HAS_CRYPTOGRAPHY = False
        super(TestVaultEditorPyCrypto, self).setUp()

    def tearDown(self):
        vault.HAS_CRYPTOGRAPHY = self.has_cryptography
        super(TestVaultEditorPyCrypto, self).tearDown()
