# (c) 2016, Matt Davis <mdavis@ansible.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time

from datetime import datetime, timedelta

from ansible.plugins.action import ActionBase
from ansible.module_utils._text import to_native

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False

    DEFAULT_REBOOT_TIMEOUT = 600
    DEFAULT_CONNECT_TIMEOUT = 5
    DEFAULT_PRE_REBOOT_DELAY = 2
    DEFAULT_POST_REBOOT_DELAY = 0
    DEFAULT_TEST_COMMAND = 'whoami'
    DEFAULT_REBOOT_MESSAGE = 'Reboot initiated by Ansible.'

    def get_system_uptime(self):
        uptime_command = '''
            Add-Type -Namespace Ansible -Name Uptime -MemberDefinition @'
            [DllImport("kernel32.dll", SetLastError=true)]
            public static extern UInt64 GetTickCount64();
            '@
            [Ansible.Uptime]::GetTickCount64()'''
        (rc, stdout, stderr) = self._connection.exec_command(uptime_command)

        if rc == 0:
            uptime = int(stdout.strip())
        else:
            raise Exception("win_reboot: failed to get host uptime info, rc: %d, stdout: %s, stderr: %s"
                            % (rc, stdout, stderr))

        return uptime

    def do_until_success_or_timeout(self, what, timeout, what_desc, fail_sleep=1):
        max_end_time = datetime.utcnow() + timedelta(seconds=timeout)

        e = None
        while datetime.utcnow() < max_end_time:
            try:
                what()
                if what_desc:
                    display.debug("win_reboot: %s success" % what_desc)
                return
            except Exception as e:
                if what_desc:
                    display.debug("win_reboot: %s fail (expected), retrying in %d seconds..." % (what_desc, fail_sleep))
                time.sleep(fail_sleep)

        raise TimedOutException("timed out waiting for %s: %s" % (what_desc, e))

    def run(self, tmp=None, task_vars=None):

        self._supports_check_mode = True
        self._supports_async = True

        if self._play_context.check_mode:
            return dict(changed=True, elapsed=0, rebooted=True)

        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        # Handle timeout parameters and its alias
        deprecated_args = {
            'shutdown_timeout': '2.5',
            'shutdown_timeout_sec': '2.5',
        }
        for arg, version in deprecated_args.items():
            if self._task.args.get(arg) is not None:
                display.warning("Since Ansible %s, %s is no longer used with win_reboot" % (arg, version))

        if self._task.args.get('connect_timeout') is not None:
            connect_timeout = int(self._task.args.get('connect_timeout', self.DEFAULT_CONNECT_TIMEOUT))
        else:
            connect_timeout = int(self._task.args.get('connect_timeout_sec', self.DEFAULT_CONNECT_TIMEOUT))

        if self._task.args.get('reboot_timeout') is not None:
            reboot_timeout = int(self._task.args.get('reboot_timeout', self.DEFAULT_REBOOT_TIMEOUT))
        else:
            reboot_timeout = int(self._task.args.get('reboot_timeout_sec', self.DEFAULT_REBOOT_TIMEOUT))

        if self._task.args.get('pre_reboot_delay') is not None:
            pre_reboot_delay = int(self._task.args.get('pre_reboot_delay', self.DEFAULT_PRE_REBOOT_DELAY))
        else:
            pre_reboot_delay = int(self._task.args.get('pre_reboot_delay_sec', self.DEFAULT_PRE_REBOOT_DELAY))

        if self._task.args.get('post_reboot_delay') is not None:
            post_reboot_delay = int(self._task.args.get('post_reboot_delay', self.DEFAULT_POST_REBOOT_DELAY))
        else:
            post_reboot_delay = int(self._task.args.get('post_reboot_delay_sec', self.DEFAULT_POST_REBOOT_DELAY))

        test_command = str(self._task.args.get('test_command', self.DEFAULT_TEST_COMMAND))
        msg = str(self._task.args.get('msg', self.DEFAULT_REBOOT_MESSAGE))

        # Get current uptime
        try:
            before_uptime = self.get_system_uptime()
        except Exception as e:
            result['failed'] = True
            result['reboot'] = False
            result['msg'] = to_native(e)
            return result

        # Initiate reboot
        (rc, stdout, stderr) = self._connection.exec_command('shutdown /r /t %d /c "%s"' % (pre_reboot_delay, msg))

        # Test for "A system shutdown has already been scheduled. (1190)" and handle it gracefully
        if rc == 1190:
            display.warning('A scheduled reboot was pre-empted by Ansible.')

            # Try to abort (this may fail if it was already aborted)
            (rc, stdout1, stderr1) = self._connection.exec_command('shutdown /a')

            # Initiate reboot again
            (rc, stdout2, stderr2) = self._connection.exec_command('shutdown /r /t %d' % pre_reboot_delay)
            stdout += stdout1 + stdout2
            stderr += stderr1 + stderr2

        if rc != 0:
            result['failed'] = True
            result['rebooted'] = False
            result['msg'] = "Shutdown command failed, error text was %s" % stderr
            return result

        start = datetime.now()

        try:
            # keep on checking system uptime with short connection responses
            def check_uptime():
                display.vvv("attempting to get system uptime")
                # override connection timeout from defaults to custom value
                try:
                    self._connection._set_connection_timeout_override(connect_timeout)
                except AttributeError:
                    display.warning("Connection plugin does not allow the connection timeout to be overridden")

                # try and get uptime
                try:
                    current_uptime = self.get_system_uptime()
                except Exception as e:
                    raise e

                if current_uptime > before_uptime:
                    raise Exception("uptime is still greater than before")

            self.do_until_success_or_timeout(check_uptime, reboot_timeout, what_desc="reboot uptime check success")

            # reset the connection to clear the custom connection timeout
            try:
                self._connection._reset()
            except AttributeError:
                pass

            # finally run test command to ensure everything is working
            def run_test_command():
                display.vvv("attempting post-reboot test command '%s'" % test_command)
                (rc, stdout, stderr) = self._connection.exec_command(test_command)

                if rc != 0:
                    raise Exception('test command failed')

            # FUTURE: ensure that a reboot has actually occurred by watching for change in last boot time fact
            # FUTURE: add a stability check (system must remain up for N seconds) to deal with self-multi-reboot updates

            self.do_until_success_or_timeout(run_test_command, reboot_timeout, what_desc="post-reboot test command success")

            result['rebooted'] = True
            result['changed'] = True

        except TimedOutException as toex:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = toex.message

        if post_reboot_delay != 0:
            display.vvv("win_reboot: waiting an additional %d seconds" % post_reboot_delay)
            time.sleep(post_reboot_delay)

        elapsed = datetime.now() - start
        result['elapsed'] = elapsed.seconds

        return result
