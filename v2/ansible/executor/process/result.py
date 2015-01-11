# (c) 2012-2014, Michael DeHaan <michael.dehaan@gmail.com>
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

import Queue
import multiprocessing
import os
import signal
import sys
import time
import traceback

HAS_ATFORK=True
try:
    from Crypto.Random import atfork
except ImportError:
    HAS_ATFORK=False

from ansible.executor.task_result import TaskResult
from ansible.playbook.handler import Handler
from ansible.playbook.task import Task

from ansible.utils.debug import debug

__all__ = ['ResultProcess']


class ResultProcess(multiprocessing.Process):
    '''
    The result worker thread, which reads results from the results
    queue and fires off callbacks/etc. as necessary.
    '''

    def __init__(self, final_q, workers):

        # takes a task queue manager as the sole param:
        self._final_q           = final_q
        self._workers           = workers
        self._cur_worker        = 0
        self._terminated        = False

        super(ResultProcess, self).__init__()

    def _send_result(self, result):
        debug("sending result: %s" % (result,))
        self._final_q.put(result, block=False)
        debug("done sending result")

    def _read_worker_result(self):
        result = None
        starting_point = self._cur_worker
        while True:
            (worker_prc, main_q, rslt_q) = self._workers[self._cur_worker]
            self._cur_worker += 1
            if self._cur_worker >= len(self._workers):
                self._cur_worker = 0

            try:
                if not rslt_q.empty():
                    debug("worker %d has data to read" % self._cur_worker)
                    result = rslt_q.get(block=False)
                    debug("got a result from worker %d: %s" % (self._cur_worker, result))
                    break
            except Queue.Empty:
                pass

            if self._cur_worker == starting_point:
                break

        return result

    def terminate(self):
        self._terminated = True
        super(ResultProcess, self).terminate()

    def run(self):
        '''
        The main thread execution, which reads from the results queue
        indefinitely and sends callbacks/etc. when results are received.
        '''

        if HAS_ATFORK:
            atfork()

        while True:
            try:
                result = self._read_worker_result()
                if result is None:
                    time.sleep(0.1)
                    continue

                host_name = result._host.get_name()

                # send callbacks, execute other options based on the result status
                if result.is_failed():
                    self._send_result(('host_task_failed', result))
                elif result.is_unreachable():
                    self._send_result(('host_unreachable', result))
                elif result.is_skipped():
                    self._send_result(('host_task_skipped', result))
                else:
                    self._send_result(('host_task_ok', result))

                    # if this task is notifying a handler, do it now
                    if result._task.notify:
                        # The shared dictionary for notified handlers is a proxy, which
                        # does not detect when sub-objects within the proxy are modified.
                        # So, per the docs, we reassign the list so the proxy picks up and
                        # notifies all other threads
                        for notify in result._task.notify:
                            self._send_result(('notify_handler', notify, result._host))

                    if 'add_host' in result._result:
                        # this task added a new host (add_host module)
                        self._send_result(('add_host', result))
                    elif 'add_group' in result._result:
                        # this task added a new group (group_by module)
                        self._send_result(('add_group', result))
                    elif 'ansible_facts' in result._result:
                        # if this task is registering facts, do that now
                        if result._task.action in ('set_fact', 'include_vars'):
                            for (key, value) in result._result['ansible_facts'].iteritems():
                                self._send_result(('set_host_var', result._host, key, value))
                        else:
                            self._send_result(('set_host_facts', result._host, result._result['ansible_facts']))

                    # if this task is registering a result, do it now
                    if result._task.register:
                        self._send_result(('set_host_var', result._host, result._task.register, result._result))

            except Queue.Empty:
                pass
            except (KeyboardInterrupt, IOError, EOFError):
                break
            except:
                # FIXME: we should probably send a proper callback here instead of
                #        simply dumping a stack trace on the screen
                traceback.print_exc()
                break

