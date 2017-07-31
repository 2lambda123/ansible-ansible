from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
import os
import subprocess
from ansible.module_utils.urls import open_url
from ansible.plugins.callback import CallbackBase


class CallbackModule(CallbackBase):
    """This is an ansible callback plugin that sends full
    play recap to github gist and sends colored notification
    to  a Slack channel after play ends.

    This plugin makes use of file `slack.json` in your playbook folder
    with following contents:
    ```json
    {
        "webhook": "Slack incoming webhook url",
        "username": "Ansible"
    }
    ```

    Output: https://gist.github.com/anonymous/f75e04a115ea86b730e41e2ef03cc5f0
    """

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'notification'
    CALLBACK_NAME = 'slack_github'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self, display=None):
        self.disabled = False
        super(CallbackModule, self).__init__(display=display)
        self.github_api = 'https://api.github.com/'
        self._log = []

    def init_config(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        config_file = os.path.join(
            playbook._basedir.encode(
                'ascii', 'ignore'), 'slack.json')
        if not os.path.isfile(config_file):
            self._display.warning(
                'File {0} not found. SlackGithub callback has been disabled'.format(config_file))
            self.disabled = True
            return
        with open(config_file) as config_file:
            self.config = json.load(config_file)
        try:
            cmd = ['git', 'config', '--get', 'user.name']
            username = subprocess.check_output(
                cmd, universal_newlines=True).split('\0')
            self.user = username[0].rstrip()
        except BaseException:
            self.user = 'Anonymous'

    def log(self, text):
        self._log.append(text)

    def send(self, color='good'):
        if self.disabled:
            return
        raw_gist = {
            'description': 'Ansible play recap',
            'public': False,
            'files': {
                'recap.md': {
                    'content': '\n'.join(
                        self._log)}}}

        data = json.dumps(raw_gist)
        try:
            response = open_url(
                self.github_api + 'gists',
                data=data,
                method='POST')
        except Exception as e:
            self._display.warning('Could not submit play recap: {0}'.format(e))

        gist = json.loads(response.read())
        url = gist[u'html_url'].encode('ascii', 'ignore')
        hosts = '*{0}*'.format(', '.join(self.play.hosts))
        message = 'Playbook *{0}* has been played against {1} by *{2}* *<{3}#file-recap-md|Details>*'.format(
            self.playbook_name, hosts, self.user, url)
        payload = {'username': self.config['username'],
                   'attachments': [{'fallback': message,
                                    'fields': [{'value': message}],
                                    'color': color,
                                    'mrkdwn_in': ['text',
                                                  'fallback',
                                                  'fields'],
                                    }],
                   'parse': 'none'}

        data = json.dumps(payload)
        try:
            response = open_url(self.config['webhook'], data=data)
        except Exception as e:
            self._display.warning(
                'Could not submit notification to Slack: {0}'.format(e))

    def v2_playbook_on_start(self, playbook):
        self.init_config(playbook)
        self.log('**Playbook**: {0}\n\n'.format(os.path.basename(playbook._file_name)))

    def v2_playbook_on_play_start(self, play):
        self.play = play
        name = play.name or 'Not specified #{0}'.format(play._uuid)
        self.log('# Play: {0}\n\n'.format(name))

    def v2_playbook_on_stats(self, stats):
        color = 'good'
        self.log('# Stats\n\n')
        hosts = sorted(stats.processed.keys())
        for host in hosts:
            summary = stats.summarize(host)
            self.log('**Host**: {0}\n'.format(host))
            for item, count in summary.items():
                self.log('> **{0}**: {1}\n\n'.format(item, count))
                if item == 'failures' and count > 0:
                    color = 'danger'
        self.send(color)

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.log('**_FAILED_ {0}** | {1}\n\n'.format(result._host.get_name(),
                                                   result._task.get_name().strip()))
        self.log(
            '```json\n{0}\n```\n\n'.format(
                json.dumps(
                    result._result,
                    indent=1,
                    sort_keys=True)))

    def v2_runner_on_ok(self, result):
        self.log('**{0}** | {1}\n\n'.format(result._host.get_name(),
                                          result._task.get_name().strip()))

    def v2_runner_on_unreachable(self, result):
        self.log('**_UNREACHABLE_ {0}** | {1}\n\n'.format(result._host.get_name(),
                                                        result._task.get_name().strip))
        self.log(
            '```json\n{0}\n```\n\n'.format(
                json.dumps(
                    result._result,
                    indent=1,
                    sort_keys=True)))
