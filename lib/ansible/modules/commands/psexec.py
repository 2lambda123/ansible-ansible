#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2018, Jordan Borean <jborean93@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


DOCUMENTATION = r'''
---
module: psexec
short_description: Runs commands on a remote Windows host based on the PsExec
  model
version_added: "2.6"
description:
- Runs a remote command from a Linux host to a Windows host without WinRM being
  set up.
- Can be run on the Ansible controller to bootstrap Windows hosts to get them
  ready for WinRM.
options:
  hostname:
    description:
    - The remote Windows host to connect to, can be either an IP address or a
      hostname.
    required: yes
  connection_username:
    description:
    - The username to use when connecting to the remote Windows host.
    - This user must be a member of the C(Administrators) group of the Windows
      host.
    - Required if the Kerberos requirements are not installed or the username
      is a local account to the Windows host.
    - Can be omitted to use the default Kerberos principal ticket in the
      local credential cache if the Kerberos library is installed.
    - If I(process_username) is not specified, then the remote process will run
      under a Network Logon under this account.
  connection_password:
    description:
    - The password for I(connection_user).
    - Required if the Kerberos requirements are not installed or the username
      is a local account to the Windows host.
    - Can be omitted to use a Kerberos principal ticket for the principal set
      by I(connection_user) if the Kerberos library is installed and the
      ticket has already been retrieved with the C(kinit) command before.
  port:
    description:
    - The port that the remote SMB service is listening on.
    default: 445
  encrypt:
    description:
    - Will use SMB encryption to encrypt the SMB messages sent to and from the
      host.
    - This requires the SMB 3 protocol which is only supported from Windows
      Server 2012 or Windows 8, older versions like Windows 7 or Windows Server
      2008 (R2) must set this to C(no) and use no encryption.
    - When setting to C(no), the packets are in plaintext and can be seend by
      anyone sniffing the network, any process options are included in this.
    type: bool
    default: 'yes'
  connection_timeout:
    description:
    - The timeout in seconds to wait when receiving the initial SMB negotiate
      response from the server.
    default: 60
  executable:
    description:
    - The executable to run on the Windows host.
    required: yes
  arguments:
    description:
    - Any arguments as a single string to use when running the executable.
  working_directory:
    description:
    - Changes the working directory set when starting the process.
    default: C:\Windows\System32
  asynchronous:
    description:
    - Will run the command as a detached process and the module returns
      immediately after starting the processs while the process continues to
      run the background.
    - The I(stdout) and I(stderr) return values will be null when this is set
      to C(yes).
    - The I(stdin) option does not work with this type of process.
    - The I(rc) return value is not set when this is C(yes)
    type: bool
    default: 'no'
  load_profile:
    description:
    - Runs the remote command with the user's profile loaded.
    type: bool
    default: 'yes'
  process_username:
    description:
    - The user to run the process as.
    - This can be set to run the process under an Interactive logon of the
      specified account which bypasses limitations of a Network logon used when
      this isn't specified.
    - If ommited then the process is run under the same account as
      I(connection_username) with a Network logon.
    - If I(encrypt) is C(no), the username and password are sent as a simple
      XOR scrambled byte string that is not encrypted. No special tools are
      required to get the username and password just knowledge of the protocol.
  process_password:
    description:
    - The password for I(process_username).
    - Required if I(process_username) is defined.
  elevated:
    description:
    - Will run the command with Administrative rights when I(process_username)
      is defined.
    - This only affects the process if C(process_username) is set, if it is not
      then the process is run under the I(connection_username) account and
      already has an elevated token to the process.
    - Cannot be C(yes) when I(limited) is also C(yes).
    type: bool
    default: 'no'
  limited:
    description:
    - Will run the command with limited rights similar to running a process
      normally when UAC is turned on.
    - This only affect the process if C(process_username) is set, if it is not
      then the process is runder the I(connection_username) account and cannot
      be run under a limited token.
    - Cannot be C(yes) when I(elevated) is also C(yes).
    type: bool
    default: 'no'
  use_system:
    description:
    - Runs the process under the local SYSTEM account instead of a normal user.
    - This option overrides C(process_username) if set to C(yes).
    - The process is run with the highest rights available to a process.
    - This can be dangerous if used incorrectly.
    type: bool
    default: 'no'
  interactive:
    description:
    - Will run the process as an interactive process that shows a process
      Window of the Windows session specified by I(interactive_session).
    - The I(stdout) and I(stderr) return values will be null when this is set
      to C(yes).
    - The I(stdin) option does not work with this type of process.
    type: bool
    default: 'no'
  interactive_session:
    description:
    - The Windows session ID to use when displaying the interactive process on
      the remote Windows host.
    - This is only valid when I(interactive) is C(yes).
    - The default is C(0) which is the console session of the Windows host.
    default: 0
  priority:
    description:
    - Set the command's priority on the Windows host.
    - See U(https://msdn.microsoft.com/en-us/library/windows/desktop/ms683211.aspx)
      for more details.
    choices:
    - above_normal
    - below_normal
    - high
    - idle
    - normal
    - realtime
    default: normal
  show_ui_on_win_logon:
    description:
    - Shows the process UI on the Winlogon secure desktop when I(use_system) is
      C(yes).
    type: bool
    default: 'no'
  process_timeout:
    description:
    - The timeout in seconds that is placed upon the running process.
    - A value of C(0) means no timeout.
    default: 0
  stdin:
    description:
    - Data to send on the stdin pipe once the process has started.
    - This option does not do anything when I(interactive) or I(asynchronous)
      is C(yes).
requirements:
- pypsexec
- smbprotocol[kerberos] for Kerberos authentication
notes:
- This module requires the Windows host to have SMB setup and the port 445
  opened on the firewall.
- This module will wait until the end process is finished unless
  I(asynchronous) is C(yes), make sure the process is run as a non-interactive
  command or send the exit command through the I(stdin) parameter.
- When connecting to a desktop version of Windows like Windows 7 or 10, either
  UAC needs to be disabled or C(LocalAccountTokenFilterPolicy) set to C(1)
  U(https://support.microsoft.com/en-us/help/951016/description-of-user-account-control-and-remote-restrictions-in-windows).
- For more information on this module and the various host requirements, see
  U(https://github.com/jborean93/pypsexec).
author:
- Jordan Borean (@jborean93)
'''

EXAMPLES = r'''
- name: run a cmd.exe command
  psexec:
    hostname: server
    connection_username: username
    connection_password: password
    executable: cmd.exe
    arguments: /c echo Hello World

- name: run a PowerShell command
  psexec:
    hostname: server.domain.local
    connection_username: username@DOMAIN.LOCAL
    connection_password: password
    executable: powershell.exe
    arguments: Write-Host Hello World

- name: send data through stdin
  psexec:
    hostname: 192.168.1.2
    connection_username: username
    connection_password: password
    executable: powershell.exe
    arguments: '-'
    stdin: |
      Write-Host Hello World
      Write-Error Error Message
      exit 0

- name: Run the process as a different user
  psexec:
    hostname: server
    connection_user: username
    connection_password: password
    executable: whoami.exe
    arguments: /all
    process_username: anotheruser
    process_password: anotherpassword

- name: Run the process asynchronously
  psexec:
    hostname: server
    connection_username: username
    connection_password: password
    executable: cmd.exe
    arguments: /c rmdir C:\temp
    asynchronous: yes

- name: Use Kerberos authentication for the connection (requires smbprotocol[kerberos])
  psexec:
    hostname: host.domain.local
    connection_username: user@DOMAIN.LOCAL
    executable: C:\some\path\to\executable.exe
    arguments: /s

- name: Disable encryption to work with WIndows 7/Server 2008 (R2)
  psexec:
    hostanme: windows-pc
    connection_username: Administrator
    connection_password: Password01
    encrypt: no
    elevated: yes
    process_username: Administrator
    process_password: Password01
    executable: powershell.exe
    arguments: (New-Object -ComObject Microsoft.Update.Session).CreateUpdateInstaller().IsBusy

- name: Download and run ConfigureRemotingForAnsible.ps1 to setup WinRM
  psexec:
    hostname: windows-pc
    connection_username: Administrator
    connection_password: Password01
    encrypt: yes
    executable: powershell.exe
    arguments: '-'
    stdin: |
      $ErrorActionPreference = "Stop"
      $sec_protocols = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::SystemDefault
      $sec_protocols = $sec_protocols -bor [Net.SecurityProtocolType]::Tls12
      [Net.ServicePointManager]::SecurityProtocol = $sec_protocols
      $url = "https://github.com/ansible/ansible/raw/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
      Invoke-Expression ((New-Object Net.WebClient).DownloadString($url))
      exit
'''

RETURN = r'''
msg:
  description: Any exception details when trying to run the process
  returned: module failed
  type: str
  sample: 'Received exception from remote PAExec service: Failed to start "invalid.exe". The system cannot find the file specified. [Err=0x2, 2]'
stdout:
  description: The stdout from the remote process
  returned: success and interactive or asynchronous is 'no'
  type: str
  sample: Hello World
stderr:
  description: The stderr from the remote process
  returned: success and interactive or asynchronous is 'no'
  type: str
  sample: Error [10] running process
pid:
  description: The process ID of the asynchronous process that was created
  returned: success and asynchronous is 'yes'
  type: int
  sample: 719
rc:
  description: The return code of the remote process
  returned: success and asynchronous is 'no'
  type: int
  sample: 0
'''

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils._text import to_bytes, to_native, to_text

try:
    from pypsexec import client
    from pypsexec.exceptions import PypsexecException, PAExecException, \
        PDUException, SCMRException
    from pypsexec.paexec import ProcessPriority
    from smbprotocol.exceptions import SMBException, SMBAuthenticationError, \
        SMBResponseException
    HAS_PYPSEXEC = True
except ImportError:
    HAS_PYPSEXEC = False

try:
    import gssapi
    # GSSAPI extension required for Kerberos Auth in SMB
    from gssapi.raw import inquire_sec_context_by_oid
    HAS_KERBEROS = True
except ImportError:
    HAS_KERBEROS = False


def remove_artifacts(module, client):
    warning_msg = "Failed to cleanup PAExec service and executable"
    try:
        client.remove_service()
    except PDUException as exc:
        module.warn("%s with RPC PDU fault: %s" % (warning_msg, to_text(exc)))
    except SCMRException as exc:
        module.warn("%s with an SCMR fault: %s" % (warning_msg, to_text(exc)))
    except PypsexecException as exc:
        module.warn("%s with generic fault: %s" % (warning_msg, to_text(exc)))
    except SMBException as exc:
        module.warn("Failed to remove PAExec executable with SMB fault: %s"
                    % to_text(exc))


def main():
    module_args = dict(
        hostname=dict(type='str', required=True),
        connection_username=dict(type='str'),
        connection_password=dict(type='str', no_log=True),
        port=dict(type='int', required=False, default=445),
        encrypt=dict(type='bool', default=True),
        connection_timeout=dict(type='int', default=60),
        executable=dict(type='str', required=True),
        arguments=dict(type='str'),
        working_directory=dict(type='str', default='C:\\Windows\\System32'),
        asynchronous=dict(type='bool', default=False),
        load_profile=dict(type='bool', default=True),
        process_username=dict(type='str'),
        process_password=dict(type='str', no_log=True),
        elevated=dict(type='bool', default=False),
        limited=dict(type='bool', default=False),
        use_system=dict(type='bool', default=False),
        interactive=dict(type='bool', default=False),
        interactive_session=dict(type='int', default=0),
        priority=dict(type='str', default='normal',
                      choices=['above_normal', 'below_normal', 'high',
                               'idle', 'normal', 'realtime']),
        show_ui_on_win_logon=dict(type='bool', default=False),
        process_timeout=dict(type='int', default=0),
        stdin=dict(type='str')
    )
    result = dict(
        changed=False,
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        required_together=[['process_username', 'process_password']]
    )

    if not HAS_PYPSEXEC:
        module.fail_json(msg='The pypsexec python module is required')

    hostname = module.params['hostname']
    connection_username = module.params['connection_username']
    connection_password = module.params['connection_password']
    port = module.params['port']
    encrypt = module.params['encrypt']
    connection_timeout = module.params['connection_timeout']
    executable = module.params['executable']
    arguments = module.params['arguments']
    working_directory = module.params['working_directory']
    asynchronous = module.params['asynchronous']
    load_profile = module.params['load_profile']
    process_username = module.params['process_username']
    process_password = module.params['process_password']
    elevated = module.params['elevated']
    limited = module.params['limited']
    use_system = module.params['use_system']
    interactive = module.params['interactive']
    interactive_session = module.params['interactive_session']

    priority = {
        "above_normal": ProcessPriority.ABOVE_NORMAL_PRIORITY_CLASS,
        "below_normal": ProcessPriority.BELOW_NORMAL_PRIORITY_CLASS,
        "high": ProcessPriority.HIGH_PRIORITY_CLASS,
        "idle": ProcessPriority.IDLE_PRIORITY_CLASS,
        "normal": ProcessPriority.NORMAL_PRIORITY_CLASS,
        "realtime": ProcessPriority.REALTIME_PRIORITY_CLASS
    }[module.params['priority']]
    show_ui_on_win_logon = module.params['show_ui_on_win_logon']

    process_timeout = module.params['process_timeout']
    stdin = module.params['stdin']

    if connection_username is None or connection_password is None and \
            not HAS_KERBEROS:
        module.fail_json(msg='The gssapi python module with the GGF extension '
                             'is required for Kerberos authentication')

    win_client = client.Client(server=hostname, username=connection_username,
                               password=connection_password, port=port,
                               encrypt=encrypt)

    try:
        win_client.connect(timeout=connection_timeout)
    except SMBAuthenticationError as exc:
        module.fail_json(msg='Failed to authenticate over SMB: %s'
                             % to_native(exc))
    except SMBResponseException as exc:
        module.fail_json(msg='Received unexpected SMB response when opening '
                             'the connection: %s' % to_native(exc))
    except SMBException as exc:
        module.fail_json(msg=to_native(exc), exception=exc)
    except PDUException as exc:
        module.fail_json(msg='Received an exception with RPC PDU message: %s'
                             % to_native(exc))
    except SCMRException as exc:
        module.fail_json(msg='Received an exception when dealing with SCMR on '
                             'the Windows host: %s' % to_native(exc))
    except PypsexecException as exc:
        module.fail_json(msg=to_native(exc), exception=exc)

    # create PAExec service and run the process
    result['changed'] = True
    b_stdin = to_bytes(stdin, encoding='utf-8') if stdin else None
    run_args = dict(
        executable=executable, arguments=arguments, asynchronous=asynchronous,
        load_profile=load_profile, interactive_session=interactive_session,
        run_elevated=elevated, run_limited=limited,
        username=process_username, password=process_password,
        use_system_account=use_system, working_dir=working_directory,
        priority=priority, show_ui_on_win_logon=show_ui_on_win_logon,
        timeout_seconds=process_timeout, stdin=b_stdin
    )
    if not module.check_mode:
        try:
            win_client.create_service()
        except PDUException as exc:
            module.fail_json(msg='Failed to create PAExec service with PDU '
                                 'fault: %s' % to_text(exc))
        except SCMRException as exc:
            module.fail_json(msg='Failed to create PAExec service with SCMR '
                                 'Error: %s' % to_text(exc))
        except PypsexecException as exc:
            module.fail_json(msg=to_text(exc), exception=exc)
        except SMBException as exc:
            module.fail_json(msg=to_text(exc), exception=exc)

        try:
            proc_result = win_client.run_executable(**run_args)
        except PAExecException as exc:
            module.fail_json(msg='Received error when running remote process: '
                                 '%s' % to_text(exc))
        except PypsexecException as exc:
            module.fail_json(msg=to_text(exc), exception=exc)
        finally:
            remove_artifacts(module, win_client)

        if asynchronous:
            result['pid'] = proc_result[2]
        elif interactive:
            result['rc'] = proc_result[2]
        else:
            result['stdout'] = proc_result[0]
            result['stderr'] = proc_result[1]
            result['rc'] = proc_result[2]

    # close the SMB connection
    try:
        win_client.disconnect()
    except SMBResponseException as exc:
        module.warn('Received an unexpected SMB response when closing the SMB '
                    'connection: %s' % to_native(exc))
    except SMBException as exc:
        module.warn('Unexpected SMB exception was raised when closing the SMB '
                    'connection: %s' % to_native(exc))
    except PDUException as exc:
        module.warn('Received an unexpected PDU fault when closing SCMR: %s'
                    % to_native(exc))
    except SCMRException as exc:
        module.warn('Received an unexpected SCMR fault when closing SCMR: %s'
                    % to_native(exc))
    except PypsexecException as exc:
        module.warn('Unexpected pypsexec exception was raised when closing '
                    'the SMB connection' % to_text(exc))

    module.exit_json(**result)


if __name__ == '__main__':
    main()
