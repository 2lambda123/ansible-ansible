
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

from os.path import basename

import cProfile
import tempfile

from ansible.errors import AnsibleParserError
from ansible.playbook.attribute import FieldAttribute
from ansible.playbook.task_include import TaskInclude
from ansible.playbook.role import Role
from ansible.playbook.role.include import RoleInclude

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

__all__ = ['IncludeRole']


class IncludeRole(TaskInclude):

    """
    A Role include is derived from a regular role to handle the special
    circumstances related to the `- include_role: ...`
    """

    BASE = ('name', 'role')  # directly assigned
    FROM_ARGS = ('tasks_from', 'vars_from', 'defaults_from')  # used to populate from dict in role
    OTHER_ARGS = ('private', 'allow_duplicates', 'profiling')  # assigned to matching property
    VALID_ARGS = tuple(frozenset(BASE + FROM_ARGS + OTHER_ARGS))  # all valid args

    # =================================================================================
    # ATTRIBUTES

    # private as this is a 'module options' vs a task property
    _allow_duplicates = FieldAttribute(isa='bool', default=None, private=True)
    _private = FieldAttribute(isa='bool', default=None, private=True)
    _profiling = FieldAttribute(isa='bool', default=None, private=True)

    def __init__(self, block=None, role=None, task_include=None):

        super(IncludeRole, self).__init__(block=block, role=role, task_include=task_include)

        self._from_files = {}
        self._parent_role = role
        self._role_name = None
        self._role_path = None
        self._play = None
        self._role = None
        self._cached_vars = {}

    def serialize(self, no_play=False):
        data = super(IncludeRole, self).serialize()
        if not self._squashed and not self._finalized:
            data['_irole_name'] = self._role_name
            if self._parent_role:
                data['_irole_prole'] = self._parent_role.serialize()
            data['_irole_path'] = self._role_path
            if getattr(self, '_role', None):
                data['_irole_drole'] = self._role.serialize()
            if getattr(self, '_play', None) and not no_play:
                # avoid deepcopy recurse errors
                self._play.unregister_dynamic_role(self)
                data['_irole_play'] = self._play.serialize(
                    skip_dynamic_roles=True)
        return data

    def __setstate__(self, sr):
        self.__init__()
        self.deserialize(sr)

    def __getstate__(self):
        sr = self.serialize()
        return sr

    def deserialize(self, data, play=None, include_deps=True):
        from ansible.playbook.play import Play
        from ansible.playbook.role import Role
        self._role_name = data.get('_irole_name', '')
        self._role_path = data.get('_irole_path', '')
        if play is None and '_irole_play' in data:
            play = Play()
            play.deserialize(data['_irole_play'])
            del data['_irole_play']
        if play is not None:
            setattr(self, '_play', play)
        if '_irole_drole' in data:
            r = Role()
            r.deserialize(data['_irole_drole'])
            setattr(self, '_role', r)
            del data['_irole_drole']
        if '_irole_prole' in data:
            r = Role()
            r.deserialize(data['_irole_prole'])
            setattr(self, '_parent_role', r)
            del data['_irole_prole']
        if play is not None:
            play.register_dynamic_role(self)
        super(IncludeRole, self).deserialize(data)

    def get_block_list(self, play, variable_manager=None, loader=None):
        self.set_play(play)
        play = self.get_play()  # may throw error if play is None
        # Get role
        ir = self.load_dynamic_role()
        # compile role with parent roles as dependencies to ensure they inherit
        # variables
        if not self._parent_role:
            dep_chain = []
        else:
            dep_chain = list(self._parent_role._parents)
            dep_chain.append(self._parent_role)

        blocks = ir.compile(play=self._play, dep_chain=dep_chain)
        for b in blocks:
            b._parent = self

        # updated available handlers in play
        handlers = ir.get_handler_blocks(play=self._play)

        play.handlers = self._play.handlers + handlers
        return blocks, handlers

    @staticmethod
    def load(data, block=None, role=None, task_include=None, variable_manager=None, loader=None):

        ir = IncludeRole(block, role, task_include=task_include).load_data(data, variable_manager=variable_manager, loader=loader)

        # Validate options
        my_arg_names = frozenset(ir.args.keys())

        # name is needed, or use role as alias
        ir._role_name = ir.args.get('name', ir.args.get('role'))
        if ir._role_name is None:
            raise AnsibleParserError("'name' is a required field for include_role.")

        # validate bad args, otherwise we silently ignore
        bad_opts = my_arg_names.difference(IncludeRole.VALID_ARGS)
        if bad_opts:
            raise AnsibleParserError('Invalid options for include_role: %s' % ','.join(list(bad_opts)))

        # build options for role includes
        for key in my_arg_names.intersection(IncludeRole.FROM_ARGS):
            from_key = key.replace('_from', '')
            ir._from_files[from_key] = basename(ir.args.get(key))

        # manual list as otherwise the options would set other task parameters we don't want.
        for option in my_arg_names.intersection(IncludeRole.OTHER_ARGS):
            setattr(ir, option, ir.args.get(option))

        return ir

    def copy(self, exclude_parent=False, exclude_tasks=False):
        # save our attrs
        role = self._role
        cachedvars = self._cached_vars
        parentrole = self._parent_role
        parent = self._parent
        play = self._play

        # be smaller for parent methods to shallow copy
        self._role = None
        self._cached_vars = {}
        self._parent = None
        self._parent_role = None
        self._play = None

        new_me = super(IncludeRole, self).copy(exclude_parent=exclude_parent, exclude_tasks=exclude_tasks)

        # restore our state
        self._role = role
        self._cached_vars = cachedvars
        self._parent_role = parentrole
        self._parent = parent
        self._play = play

        new_me.statically_loaded = self.statically_loaded
        new_me._from_files = self._from_files.copy()
        new_me._parent_role = self._parent_role
        new_me._role_name = self._role_name
        new_me._role_path = self._role_path
        new_me.private = self.private
        new_me._play = self._play
        new_me._role = self._role
        return new_me

    def __deepcopy__(self, memo):
        ret = self.deserialize(self.serialize())
        memo[id(self)] = ret
        return ret

    def load_dynamic_role(self, allow_duplicates=None):
        pr = None
        if self.profiling:
            pr = cProfile.Profile()
            pr.enable()
        if allow_duplicates is None:
            allow_duplicates = self.allow_duplicates
        play = self.get_play()
        variable_manager = self.get_variable_manager()
        loader = variable_manager._loader
        # build role
        ri = RoleInclude.load(self._role_name,
                              play=play,
                              variable_manager=variable_manager,
                              loader=loader)
        if self.vars:
            v = self.vars.copy()
            # bypass vars from include_role itself
            for k in [
                'name', 'private', 'allow_duplicates',
                'defaults_from', 'tasks_from', 'vars_from'
            ]:
                v.pop(k, None)
            ri.vars.update(v)
        role = Role.load(
            ri, play, parent_role=self._parent_role,
            from_files=self._from_files)
        # proxy allow_duplicates attribute to role if explicitly set
        if self.allow_duplicates is not None:
            role._metadata.allow_duplicates = self.allow_duplicates
        # in any case sync allow_duplicates between the role and this include statement
        # This is the side effect if we didnt explicitly setted the allow_duplicates attribute
        # to fallback on the included role setting
        if self.allow_duplicates is None and role._metadata:
            self.allow_duplicates = role._metadata.allow_duplicates
        self._role_path = role._role_path
        self.set_dynamic_role(role)
        play.register_dynamic_role(self)
        if self.profiling:
            pr.disable()
            fich, fic = tempfile.mkstemp()
            pr.dump_stats(fic + '_role_astat')
        return role

    def set_play(self, play):
        self._play = play

    def get_play(self):
        if self._play is None:
            raise ValueError('Play is not initialised')
        return self._play

    def set_dynamic_role(self, value):
        self._role = value

    def get_dynamic_role(self):
        if self._role is None:
            raise ValueError('Role is not initialised, call load !')
        return self._role

    @property
    def is_loaded(self):
        return self._role is not None

    def cache_get(self, key, kval, func, *a, **kw):
        try:
            cache = self._cached_vars[key]
        except KeyError:
            cache = self._cached_vars[key] = {}
        try:
            ret = cache[kval]
        except KeyError:
            cache[kval] = ret = func(*a, **kw)
        return ret

    def get_default_vars(self, dep_chain=None):
        cache_key = (self.is_loaded, dep_chain and tuple(dep_chain) or None)

        def func(dep_chain, *a, **kw):
            if not self.is_loaded:
                return dict()
            if dep_chain is None:
                dep_chain = self.get_dep_chain()
            ret = self.get_dynamic_role().get_default_vars(dep_chain=dep_chain)
            return ret
        return self.cache_get('default', cache_key, func, dep_chain)

    def get_vars(self, include_params=True):
        cache_key = (include_params, self.is_loaded)

        def func(include_params, *a, **kw):
            ret = TaskInclude.get_vars(self, include_params=include_params)
            if self.is_loaded:  # not yet loaded skip
                ret.update(
                    self.get_dynamic_role().get_vars(include_params=include_params)
                )
            return ret
        return self.cache_get('vars', cache_key, func, include_params)

    def get_include_params(self):
        cache_key = bool(self._parent_role)

        def func(*a, **kw):
            v = super(IncludeRole, self).get_include_params()
            if self._parent_role:
                v.update(self._parent_role.get_role_params())
            return v
        return self.cache_get('include_params', cache_key, func)
