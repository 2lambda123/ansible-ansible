# (c) 2014, James Tanner <tanner.jc@gmail.com>
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
#
# ansible-vault is a script that encrypts/decrypts YAML files. See
# http://docs.ansible.com/playbooks_vault.html for more details.

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os
import sys

from ansible.errors import AnsibleError, AnsibleOptionsError
from ansible.parsing.dataloader import DataLoader
from ansible.parsing.vault import VaultEditor
from ansible.cli import CLI
from ansible.module_utils._text import to_text, to_bytes

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class VaultCLI(CLI):
    """ Vault command line class """

    VALID_ACTIONS = ("create", "decrypt", "edit", "encrypt", "encrypt_string", "rekey", "view")

    FROM_STDIN = "stdin"
    FROM_ARGS = "the command line args"
    FROM_PROMPT = "the interactive prompt"

    def __init__(self, args):

        self.vault_pass = None
        self.new_vault_pass = None

        self.encrypt_string_read_stdin = False

        super(VaultCLI, self).__init__(args)

    def parse(self):

        self.parser = CLI.base_parser(
            vault_opts=True,
            usage = "usage: %%prog [%s] [--help] [options] vaultfile.yml" % "|".join(self.VALID_ACTIONS),
            epilog = "\nSee '%s <command> --help' for more information on a specific command.\n\n" % os.path.basename(sys.argv[0])
        )

        self.set_action()

        # options specific to self.actions
        if self.action == "create":
            self.parser.set_usage("usage: %prog create [options] file_name")
        elif self.action == "decrypt":
            self.parser.set_usage("usage: %prog decrypt [options] file_name")
        elif self.action == "edit":
            self.parser.set_usage("usage: %prog edit [options] file_name")
        elif self.action == "view":
            self.parser.set_usage("usage: %prog view [options] file_name")
        elif self.action == "encrypt":
            self.parser.set_usage("usage: %prog encrypt [options] file_name")
        # I have no prefence for either dash or underscore
        elif self.action == "encrypt_string":
            self.parser.add_option('-p', '--prompt', dest='encrypt_string_prompt',
                                   action='store_true',
                                   help="Prompt for the string to encrypt")
            self.parser.set_usage("usage: %prog encrypt-string [--prompt] [options] string_to_encrypt")
        elif self.action == "rekey":
            self.parser.set_usage("usage: %prog rekey [options] file_name")

        super(VaultCLI, self).parse()

        display.verbosity = self.options.verbosity

        can_output = ['encrypt', 'decrypt', 'encrypt_string']

        if self.action not in can_output:
            if self.options.output_file:
                raise AnsibleOptionsError("The --output option can be used only with ansible-vault %s" % '/'.join(can_output))
            if len(self.args) == 0:
                raise AnsibleOptionsError("Vault requires at least one filename as a parameter")
        else:
            # This restriction should remain in place until it's possible to
            # load multiple YAML records from a single file, or it's too easy
            # to create an encrypted file that can't be read back in. But in
            # the meanwhile, "cat a b c|ansible-vault encrypt --output x" is
            # a workaround.
            if self.options.output_file and len(self.args) > 1:
                raise AnsibleOptionsError("At most one input file may be used with the --output option")

        #if '-' in self.args or len(self.args) == 0:
        if '-' in self.args:
            self.encrypt_string_read_stdin = True

        # TODO: prompting from stdin and reading from stdin seem
        #       mutually exclusive, but verify that.
        if self.options.encrypt_string_prompt and self.encrypt_string_read_stdin:
            raise AnsibleOptionsError('The --prompt option is not supported if also reading input from stdin')

    def run(self):

        super(VaultCLI, self).run()
        loader = DataLoader()

        # set default restrictive umask
        old_umask = os.umask(0o077)

        if self.options.vault_password_file:
            # read vault_pass from a file
            self.vault_pass = CLI.read_vault_password_file(self.options.vault_password_file, loader)

        if self.options.new_vault_password_file:
            # for rekey only
            self.new_vault_pass = CLI.read_vault_password_file(self.options.new_vault_password_file, loader)

        if not self.vault_pass or self.options.ask_vault_pass:
            self.vault_pass = self.ask_vault_passwords()

        if not self.vault_pass:
            raise AnsibleOptionsError("A password is required to use Ansible's Vault")

        if self.action == 'rekey':
            if not self.new_vault_pass:
                self.new_vault_pass = self.ask_new_vault_passwords()
            if not self.new_vault_pass:
                raise AnsibleOptionsError("A password is required to rekey Ansible's Vault")

        if self.action == 'encrypt_string':
            if self.options.encrypt_string_prompt:
                self.encrypt_string_prompt = True

        self.editor = VaultEditor(self.vault_pass)

        self.execute()

        # and restore umask
        os.umask(old_umask)

    def execute_encrypt(self):

        if len(self.args) == 0 and sys.stdin.isatty():
            display.display("Reading plaintext input from stdin", stderr=True)

        for f in self.args or ['-']:
            self.editor.encrypt_file(f, output_file=self.options.output_file)

        if sys.stdout.isatty():
            display.display("Encryption successful", stderr=True)

    def format_ciphertext_yaml(self, b_ciphertext, indent=None):
        indent = indent or 10
        block_format_header = "!vault-encrypted |"
        lines = []
        vault_ciphertext = to_text(b_ciphertext)

        lines.append(block_format_header)
        for line in vault_ciphertext.splitlines():
            lines.append('%s%s' % (' ' * indent, line))

        yaml_ciphertext = '\n'.join(lines)
        return yaml_ciphertext

    def execute_encrypt_string(self):

        # TODO: encoding rules for to_bytes

        b_plaintext = None

        # Holds tuples (the_text, the_source_of_the_string).
        b_plaintext_list = []

        # remove the non-option '-' arg (used to indicate 'read from stdin') from the candidate args so
        # we dont add it to the plaintext list
        args = [x for x in self.args if x != '-']

        if self.options.encrypt_string_prompt:
            msg = "string to encrypt:"

            # could use private=True for shadowed input if useful
            prompt_response = display.prompt(msg)

            if prompt_response == '':
                raise AnsibleOptionsError('The plaintext provided from the prompt was empty, not encrypting')

            b_plaintext = to_bytes(prompt_response)
            b_plaintext_list.append((b_plaintext, self.FROM_PROMPT))

        if self.encrypt_string_read_stdin:
            if sys.stdout.isatty():
                display.display("Reading plaintext input from stdin. (ctrl-d to end input)", stderr=True)

            stdin_text = sys.stdin.read()
            if stdin_text == '':
                raise AnsibleOptionsError('stdin was empty, not encrypting')

            b_plaintext = to_bytes(stdin_text)
            b_plaintext_list.append((b_plaintext, self.FROM_STDIN))

        for plaintext in args:
            if plaintext == '':
                raise AnsibleOptionsError('The plaintext provided from the command line args was empty, not encrypting')

            b_plaintext = to_bytes(plaintext)
            b_plaintext_list.append((b_plaintext, self.FROM_ARGS))


        show_delimiter = False
        if len(b_plaintext_list) > 1:
            show_delimiter = True

        # order of args seem important
        # Or maybe just only support one string...
        for index, b_plaintext_info in enumerate(b_plaintext_list):
            # (the text itself, which input it came from)
            b_plaintext, src = b_plaintext_info
            b_ciphertext = self.editor.encrypt_bytes(b_plaintext)

            yaml_text = self.format_ciphertext_yaml(b_ciphertext)
            if show_delimiter:
                sys.stderr.write('# The encrypted version of the string #%d from %s.\n' % ((index + 1), src))
            print(yaml_text)
        # if '--prompt', prompt for string

        if sys.stdout.isatty():
            display.display("Encryption successful", stderr=True)

        # TODO: write out the block of yaml to be cut and paste
        # TODO: offer block or string ala eyaml
        # TODO: or cli --block/--string for just one
        # TODO: make sure stdout is clean and can be subbed into file by script

    def execute_decrypt(self):

        if len(self.args) == 0 and sys.stdin.isatty():
            display.display("Reading ciphertext input from stdin", stderr=True)

        for f in self.args or ['-']:
            self.editor.decrypt_file(f, output_file=self.options.output_file)

        if sys.stdout.isatty():
            display.display("Decryption successful", stderr=True)

    def execute_create(self):

        if len(self.args) > 1:
            raise AnsibleOptionsError("ansible-vault create can take only one filename argument")

        self.editor.create_file(self.args[0])

    def execute_edit(self):
        for f in self.args:
            self.editor.edit_file(f)

    def execute_view(self):

        for f in self.args:
            # Note: vault should return byte strings because it could encrypt
            # and decrypt binary files.  We are responsible for changing it to
            # unicode here because we are displaying it and therefore can make
            # the decision that the display doesn't have to be precisely what
            # the input was (leave that to decrypt instead)
            self.pager(to_text(self.editor.plaintext(f)))

    def execute_rekey(self):
        for f in self.args:
            if not (os.path.isfile(f)):
                raise AnsibleError(f + " does not exist")

        for f in self.args:
            self.editor.rekey_file(f, self.new_vault_pass)

        display.display("Rekey successful", stderr=True)
