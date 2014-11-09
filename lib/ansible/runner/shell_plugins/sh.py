# (c) 2014, Chris Church <chris@ninemoreminutes.com>
#
# This file is part of Ansible.
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
import pipes
import ansible.constants as C

class ShellModule(object):

    def env_prefix(self, **kwargs):
        '''Build command prefix with environment variables.'''
        env = dict(
            LANG     = C.DEFAULT_MODULE_LANG,
            LC_CTYPE = C.DEFAULT_MODULE_LANG,
        )
        env.update(kwargs)
        return ' '.join(['%s=%s' % (k, pipes.quote(unicode(v))) for k,v in env.items()])

    def join_path(self, *args):
        return os.path.join(*args)

    def path_has_trailing_slash(self, path):
        return path.endswith('/')

    def chmod(self, mode, path):
        path = pipes.quote(path)
        return 'chmod %s %s' % (mode, path)

    def remove(self, path, recurse=False):
        path = pipes.quote(path)
        if recurse:
            return "rm -rf %s >/dev/null 2>&1" % path
        else:
            return "rm -f %s >/dev/null 2>&1" % path

    def mkdtemp(self, basefile=None, system=False, mode=None):
        if not basefile:
            basefile = 'ansible-tmp-%s-%s' % (time.time(), random.randint(0, 2**48))
        basetmp = self.join_path(C.DEFAULT_REMOTE_TMP, basefile)
        if system and basetmp.startswith('$HOME'):
            basetmp = self.join_path('/tmp', basefile)
        cmd = 'mkdir -p %s' % basetmp
        if mode:
            cmd += ' && chmod %s %s' % (mode, basetmp)
        cmd += ' && echo %s' % basetmp
        return cmd

    def checksum(self, path, python_interp):
        path = pipes.quote(path)
        # The following test needs to be SH-compliant.  BASH-isms will
        # not work if /bin/sh points to a non-BASH shell.
        test = "rc=0; [ -r \"%s\" ] || rc=2; [ -f \"%s\" ] || rc=1; [ -d \"%s\" ] && echo 3 && exit 0" % ((path,) * 3)
        csums = [
            "(%s -c 'import hashlib; print(hashlib.sha1(open(\"%s\", \"rb\").read()).hexdigest())' 2>/dev/null)" % (python_interp, path),      # Python > 2.4 (including python3)
            "(%s -c 'import sha; print(sha.sha(open(\"%s\", \"rb\").read()).hexdigest())' 2>/dev/null)" % (python_interp, path),        # Python == 2.4
        ]

        cmd = " || ".join(csums)
        cmd = "%s; %s || (echo \"${rc}  %s\")" % (test, cmd, path)
        return cmd

    def build_module_command(self, env_string, shebang, cmd, rm_tmp=None):
        cmd_parts = [env_string.strip(), shebang.replace("#!", "").strip(), cmd]
        new_cmd = " ".join(cmd_parts)
        if rm_tmp:
            new_cmd = '%s; rm -rf %s >/dev/null 2>&1' % (new_cmd, rm_tmp)
        return new_cmd
