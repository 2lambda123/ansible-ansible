# (c) 2012, Michael DeHaan <michael.dehaan@gmail.com>
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

import os

from ansible import constants as C
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):
    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' handler for file transfer operations '''

        # FIXME: noop stuff still needs to be sorted out
        #if self.runner.noop_on_check(inject):
        #    # in check mode, always skip this module
        #    return ReturnData(conn=conn, comm_ok=True,
        #                      result=dict(skipped=True, msg='check mode not supported for this module'))

        if not tmp:
            tmp = self._make_tmp_path()

        creates = self._task.args.get('creates')
        if creates:
            # do not run the command if the line contains creates=filename
            # and the filename already exists. This allows idempotence
            # of command executions.
            result = self._execute_module(module_name='stat', module_args=dict(path=creates), tmp=tmp, persist_files=True)
            stat = result.get('stat', None)
            if stat and stat.get('exists', False):
                return dict(skipped=True, msg=("skipped, since %s exists" % creates))

        removes = self._task.args.get('removes')
        if removes:
            # do not run the command if the line contains removes=filename
            # and the filename does not exist. This allows idempotence
            # of command executions.
            result = self._execute_module(module_name='stat', module_args=dict(path=removes), tmp=tmp, persist_files=True)
            stat = result.get('stat', None)
            if stat and not stat.get('exists', False):
                return dict(skipped=True, msg=("skipped, since %s does not exist" % removes))

        # the script name is the first item in the raw params, so we split it
        # out now so we know the file name we need to transfer to the remote,
        # and everything else is an argument to the script which we need later
        # to append to the remote command
        parts  = self._task.args.get('_raw_params', '').strip().split()
        source = parts[0]
        args   = ' '.join(parts[1:])

        # FIXME: need to sort out all the _original_file stuff still
        #if '_original_file' in task_vars:
        #    source = self._loader.path_dwim_relative(inject['_original_file'], 'files', source, self.runner.basedir)
        #else:
        #    source = self._loader.path_dwim(self.runner.basedir, source)
        source = self._loader.path_dwim(source)

        # transfer the file to a remote tmp location
        tmp_src = self._shell.join_path(tmp, os.path.basename(source))
        self._connection.put_file(source, tmp_src)

        sudoable = True
        # set file permissions, more permissive when the copy is done as a different user
        if ((self._connection_info.sudo and self._connection_info.sudo_user != 'root') or
            (self._connection_info.su and self._connection_info.su_user != 'root')):
            chmod_mode = 'a+rx'
            sudoable = False
        else:
            chmod_mode = '+rx'
        self._remote_chmod(tmp, chmod_mode, tmp_src, sudoable=sudoable)

        # add preparation steps to one ssh roundtrip executing the script
        env_string = self._compute_environment_string()
        script_cmd = ' '.join([env_string, tmp_src, args])
        
        result = self._low_level_execute_command(cmd=script_cmd, tmp=None, sudoable=sudoable)

        # clean up after
        if tmp and "tmp" in tmp and not C.DEFAULT_KEEP_REMOTE_FILES:
            self._remove_tmp_path(tmp)

        result['changed'] = True

        return result
