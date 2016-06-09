#
# (c) 2015 Peter Sprygada, <psprygada@ansible.com>
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
#

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.basic import env_fallback, get_exception
from ansible.module_utils.shell import Shell, ShellError, HAS_PARAMIKO

NET_TRANSPORT_ARGS = dict(
    host=dict(required=True),
    port=dict(type='int'),
    username=dict(fallback=(env_fallback, ['ANSIBLE_NET_USERNAME'])),
    password=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_PASSWORD'])),
    ssh_keyfile=dict(fallback=(env_fallback, ['ANSIBLE_NET_SSH_KEYFILE']), type='path'),
    authorize=dict(default=False, fallback=(env_fallback, ['ANSIBLE_NET_AUTHORIZE']), type='bool'),
    auth_pass=dict(no_log=True, fallback=(env_fallback, ['ANSIBLE_NET_AUTH_PASS'])),
    provider=dict(type='dict'),
    transport=dict(choices=list()),
    timeout=dict(default=10, type='int')
)

NET_CONNECTION_ARGS = dict()

NET_CONNECTIONS = dict()


def to_list(val):
    if isinstance(val, (list, tuple)):
        return list(val)
    elif val is not None:
        return [val]
    else:
        return list()

class NetworkError(Exception):

    def __init__(self, msg, **kwargs):
        super(NetworkError, self).__init__(msg)
        self.kwargs = kwargs

class NetworkModule(AnsibleModule):

    def __init__(self, *args, **kwargs):
        super(NetworkModule, self).__init__(*args, **kwargs)
        self._config = None

    @property
    def config(self):
        if not self._config:
            self._config = self.get_config()
        return self._config

    def _load_params(self):
        super(NetworkModule, self)._load_params()
        provider = self.params.get('provider') or dict()
        for key, value in provider.items():
            for args in [NET_TRANSPORT_ARGS, NET_CONNECTION_ARGS]:
                if key in args:
                    if self.params.get(key) is None and value is not None:
                        self.params[key] = value

    def invoke(self, method, *args, **kwargs):
        try:
            kwargs['params'] = self.params
            return method(*args, **kwargs)
        except AttributeError:
            if kwargs.get('raise_exception'):
                raise
            else:
                exc = get_exception()
                self.fail_json(msg='failed to execute %s' % method.__name__, exc=str(exc))
        except NetworkError:
            if kwargs.get('raise_exception'):
                raise
            else:
                exc = get_exception()
                self.fail_json(msg=exc.message, **exc.kwargs)

    def connect(self):
        return self.invoke(self.connection.connect)

    def disconnect(self):
        return self.invoke(self.connection.disconnect)

    def authorize(self):
        return self.invoke(self.connection.authorize)

    def run_commands(self, commands, **kwargs):
        commands = to_list(commands)
        return self.invoke(self.connection.run_commands, commands, **kwargs)

    def configure(self, commands, **kwargs):
        return self.load_config(commands, **kwargs)

    def load_config(self, commands, *args, **kwargs):
        commands = to_list(commands)
        return self.invoke(self.connection.load_config, commands, *args, **kwargs)

    def get_config(self, **kwargs):
        return self.invoke(self.connection.get_config, **kwargs)

    def commit_config(self, *args, **kwargs):
        return self.invoke(self.connection.commit_config, *args, **kwargs)


class NetCli(object):
    """Basic paramiko-based ssh transport any NetworkModule can use."""
    def __init__(self):
        if not HAS_PARAMIKO:
            raise NetworkError(
                msg='paramiko is required but does not appear to be installed.  '
                'It can be installed using  `pip install paramiko`'
            )

        self.shell = None

    def connect(self, params, kickstart, **kwargs):
        host = params['host']
        port = params.get('port') or 22

        username = params['username']
        password = params.get('password')
        key_file = params.get('ssh_keyfile')
        timeout = params['timeout']

        try:
            self.shell = Shell(
                kickstart=kickstart,
                prompts_re=self.CLI_PROMPTS_RE,
                errors_re=self.CLI_ERRORS_RE,
            )
            self.shell.open(
                host, port=port, username=username, password=password,
                key_filename=key_file, timeout=timeout,
            )
        except ShellError:
            exc = get_exception()
            raise NetworkError(
                msg='failed to connect to %s:%s' % (host, port), exc=str(exc)
            )

    def disconnect(self, **kwargs):
        self.shell.close()

    def run_commands(self, commands, **kwargs):
        try:
            return self.shell.send(commands)
        except ShellError:
            exc = get_exception()
            raise NetworkError(exc.message, commands=commands)


class NetCli(object):
    """Basic paramiko-based ssh transport any NetworkModule can use."""
    def __init__(self):
        if not HAS_PARAMIKO:
            raise NetworkError(
                msg='paramiko is required but does not appear to be installed.  '
                'It can be installed using  `pip install paramiko`'
            )

        self.shell = None

    def connect(self, params, kickstart, **kwargs):
        host = params['host']
        port = params.get('port') or 22

        username = params['username']
        password = params.get('password')
        key_file = params.get('ssh_keyfile')
        timeout = params['timeout']

        try:
            self.shell = Shell(
                kickstart=kickstart,
                prompts_re=self.CLI_PROMPTS_RE,
                errors_re=self.CLI_ERRORS_RE,
            )
            self.shell.open(
                host, port=port, username=username, password=password,
                key_filename=key_file, timeout=timeout,
            )
        except ShellError:
            exc = get_exception()
            raise NetworkError(
                msg='failed to connect to %s:%s' % (host, port), exc=str(exc)
            )

    def disconnect(self, **kwargs):
        self.shell.close()

    def run_commands(self, commands, **kwargs):
        try:
            return self.shell.send(commands)
        except ShellError:
            exc = get_exception()
            raise NetworkError(exc.message, commands=commands)


def get_module(connect_on_load=True, **kwargs):
    argument_spec = NET_TRANSPORT_ARGS.copy()
    argument_spec['transport']['choices'] = NET_CONNECTIONS.keys()
    argument_spec.update(NET_CONNECTION_ARGS.copy())

    if kwargs.get('argument_spec'):
        argument_spec.update(kwargs['argument_spec'])
    kwargs['argument_spec'] = argument_spec

    module = NetworkModule(**kwargs)

    try:
        transport = module.params['transport'] or '__default__'
        cls = NET_CONNECTIONS[transport]
        module.connection = cls()
    except KeyError:
        module.fail_json(msg='Unknown transport or no default transport specified')
    except TypeError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    try:
        module.connect()
        if module.params['authorize']:
            module.authorize()
    except NetworkError:
        exc = get_exception()
        module.fail_json(msg=exc.message)

    return module

def register_transport(transport, default=False):
    def register(cls):
        NET_CONNECTIONS[transport] = cls
        if default:
            NET_CONNECTIONS['__default__'] = cls
        return cls
    return register

def add_argument(key, value):
    NET_CONNECTION_ARGS[key] = value

