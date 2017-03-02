"""Execute Ansible sanity tests."""

from __future__ import absolute_import, print_function

import datetime
import glob
import json
import os
import re
import textwrap

from lib.util import (
    ApplicationError,
    SubprocessError,
    display,
    run_command,
    deepest_path,
)

from lib.ansible_util import (
    ansible_environment,
)

from lib.target import (
    walk_external_targets,
    walk_internal_targets,
    walk_sanity_targets,
)

from lib.executor import (
    detect_changes,
    get_changes_filter,
    AllTargetsSkipped,
    Delegate,
    install_command_requirements,
    SUPPORTED_PYTHON_VERSIONS,
    intercept_command,
    SanityConfig,
)

def command_sanity(args):
    """
    :type args: SanityConfig
    """
    changed_paths = detect_changes(args)
    changes = get_changes_filter(args, changed_paths)
    require = (args.require or []) + changes
    targets = SanityTargets(args.include, args.exclude, require)

    if not targets.include:
        raise AllTargetsSkipped()

    if args.delegate:
        raise Delegate(require=changes)

    install_command_requirements(args)

    tests = sanity_get_tests()

    if args.test:
        tests = [t for t in tests if t.name in args.test]

    if args.skip_test:
        tests = [t for t in tests if t.name not in args.skip_test]

    total = 0
    failed = []

    for test in tests:
        if args.list_tests:
            display.info(test.name)
            continue

        if test.intercept:
            versions = SUPPORTED_PYTHON_VERSIONS
        else:
            versions = None,

        for version in versions:
            if args.python and version and version != args.python:
                continue

            display.info('Sanity check using %s%s' % (test.name, ' with Python %s' % version if version else ''))

            if test.script:
                result = test.func(args, targets, test.script)
            elif test.intercept:
                result = test.func(args, targets, python_version=version)
            else:
                result = test.func(args, targets)

            result.write(args, changed_paths)

            total += 1

            if isinstance(result, SanityError):
                failed.append(result.test)

    if failed:
        raise ApplicationError('The %d sanity test(s) listed below (out of %d) failed. See error output above for details.\n%s' % (
            len(failed), total, '\n'.join(failed)))


def command_sanity_code_smell(args, _, script):
    """
    :type args: SanityConfig
    :type _: SanityTargets
    :type script: str
    :rtype: SanityResult
    """
    test = os.path.splitext(os.path.basename(script))[0]

    cmd = [script]
    env = ansible_environment(args)

    try:
        stdout, stderr = run_command(args, cmd, env=env, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status:
        summary = str(SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout))
        return SanityError(test, summary=summary)

    return SanitySuccess(test)


def command_sanity_validate_modules(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'validate-modules'
    env = ansible_environment(args)

    paths = [deepest_path(i.path, 'lib/ansible/modules/') for i in targets.include_external]
    paths = sorted(set(p for p in paths if p))

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'test/sanity/validate-modules/validate-modules',
        '--format', 'json',
    ] + paths

    with open('test/sanity/validate-modules/skip.txt', 'r') as skip_fd:
        skip_paths = skip_fd.read().splitlines()

    skip_paths += [e.path for e in targets.exclude_external]

    if skip_paths:
        cmd += ['--exclude', '^(%s)' % '|'.join(skip_paths)]

    if args.base_branch:
        cmd.extend([
            '--base-branch', args.base_branch,
        ])
    else:
        display.warning('Cannot perform module comparison against the base branch. Base branch not detected when running locally.')

    try:
        stdout, stderr = run_command(args, cmd, env=env, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status not in (0, 3):
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    messages = json.loads(stdout)

    results = []

    for filename in messages:
        output = messages[filename]

        for item in output['errors']:
            results.append(SanityMessage(
                path=filename,
                line=int(item['line']) if 'line' in item else 0,
                column=int(item['column']) if 'column' in item else 0,
                level='error',
                code='E%s' % item['code'],
                message=item['msg'],
            ))

    if results:
        return SanityError(test, messages=results)

    return SanitySuccess(test)


def command_sanity_shellcheck(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'shellcheck'

    with open('test/sanity/shellcheck/skip.txt', 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    with open('test/sanity/shellcheck/exclude.txt', 'r') as exclude_fd:
        exclude = set(exclude_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.sh' and i.path not in skip_paths)

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'shellcheck',
        '-e', ','.join(sorted(exclude)),
        '--format', 'json',
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr or status > 1:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr, stdout=stdout)

    if args.explain:
        return SanitySkipped(test)

    results = json.loads(stdout)

    results = [SanityMessage(
        message=r['message'],
        path=r['file'],
        line=r['line'],
        column=r['column'],
        level=r['level'],
        code='SC%s' % r['code'],
    ) for r in results]

    if results:
        return SanityError(test, messages=results)

    return SanitySuccess(test)


def command_sanity_pep8(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'pep8'

    skip_path = 'test/sanity/pep8/skip.txt'
    legacy_path = 'test/sanity/pep8/legacy-files.txt'

    with open(skip_path, 'r') as skip_fd:
        skip_paths = set(skip_fd.read().splitlines())

    with open(legacy_path, 'r') as legacy_fd:
        legacy_paths = set(legacy_fd.read().splitlines())

    with open('test/sanity/pep8/legacy-ignore.txt', 'r') as ignore_fd:
        legacy_ignore = set(ignore_fd.read().splitlines())

    with open('test/sanity/pep8/current-ignore.txt', 'r') as ignore_fd:
        current_ignore = sorted(ignore_fd.read().splitlines())

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] == '.py' and i.path not in skip_paths)

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'pep8',
        '--max-line-length', '160',
        '--config', '/dev/null',
        '--ignore', ','.join(sorted(current_ignore)),
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr)

    if args.explain:
        return SanitySkipped(test)

    pattern = '^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): (?P<code>[WE][0-9]{3}) (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    results = [SanityMessage(
        message=r['message'],
        path=r['path'],
        line=int(r['line']),
        column=int(r['column']),
        level='warning' if r['code'].startswith('W') else 'error',
        code=r['code'],
    ) for r in results]

    failed_result_paths = set([result.path for result in results])
    passed_legacy_paths = set([path for path in paths if path in legacy_paths and path not in failed_result_paths])

    errors = []
    summary = {}

    for path in sorted(passed_legacy_paths):
        # Keep files out of the list which no longer require the relaxed rule set.
        errors.append(SanityMessage(path, 'Passes current rule set. Remove from legacy list (%s).' % legacy_path))

    for path in sorted(skip_paths):
        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append(SanityMessage(path, 'Does not exist. Remove from skip list (%s).' % skip_path))

    for path in sorted(legacy_paths):
        if not os.path.exists(path):
            # Keep files out of the list which no longer exist in the repo.
            errors.append(SanityMessage(path, 'Does not exist. Remove from legacy list (%s).' % legacy_path))

    for result in results:
        if result.path in legacy_paths and result.code in legacy_ignore:
            # Files on the legacy list are permitted to have errors on the legacy ignore list.
            # However, we want to report on their existence to track progress towards eliminating these exceptions.
            display.info('PEP 8: %s (legacy)' % result, verbosity=3)

            key = '%s %s' % (result.code, re.sub('[0-9]+', 'NNN', result.message))

            if key not in summary:
                summary[key] = 0

            summary[key] += 1
        else:
            # Files not on the legacy list and errors not on the legacy ignore list are PEP 8 policy errors.
            errors.append(result)

    if summary:
        lines = []
        count = 0

        for key in sorted(summary):
            count += summary[key]
            lines.append('PEP 8: %5d %s' % (summary[key], key))

        display.info('PEP 8: There were %d different legacy issues found (%d total):' % (len(summary), count), verbosity=1)
        display.info('PEP 8: Count Code Message', verbosity=1)

        for line in lines:
            display.info(line, verbosity=1)

    if errors:
        return SanityError(test, messages=errors)

    return SanitySuccess(test)


def command_sanity_yamllint(args, targets):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :rtype: SanityResult
    """
    test = 'yamllint'

    paths = sorted(i.path for i in targets.include if os.path.splitext(i.path)[1] in ('.yml', '.yaml'))

    if not paths:
        return SanitySkipped(test)

    cmd = [
        'yamllint',
        '--format', 'parsable',
    ] + paths

    try:
        stdout, stderr = run_command(args, cmd, capture=True)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if stderr:
        raise SubprocessError(cmd=cmd, status=status, stderr=stderr)

    if args.explain:
        return SanitySkipped(test)

    pattern = r'^(?P<path>[^:]*):(?P<line>[0-9]+):(?P<column>[0-9]+): \[(?P<level>warning|error)\] (?P<message>.*)$'

    results = [re.search(pattern, line).groupdict() for line in stdout.splitlines()]

    results = [SanityMessage(
        message=r['message'],
        path=r['path'],
        line=int(r['line']),
        column=int(r['column']),
        level=r['level'],
    ) for r in results]

    if results:
        return SanityError(test, messages=results)

    return SanitySuccess(test)


def command_sanity_ansible_doc(args, targets, python_version):
    """
    :type args: SanityConfig
    :type targets: SanityTargets
    :type python_version: str
    :rtype: SanityResult
    """
    test = 'ansible-doc'

    with open('test/sanity/ansible-doc/skip.txt', 'r') as skip_fd:
        skip_modules = set(skip_fd.read().splitlines())

    modules = sorted(set(m for i in targets.include_external for m in i.modules) -
                     set(m for i in targets.exclude_external for m in i.modules) -
                     skip_modules)

    if not modules:
        return SanitySkipped(test)

    env = ansible_environment(args)
    cmd = ['ansible-doc'] + modules

    try:
        stdout, stderr = intercept_command(args, cmd, env=env, capture=True, python_version=python_version)
        status = 0
    except SubprocessError as ex:
        stdout = ex.stdout
        stderr = ex.stderr
        status = ex.status

    if status:
        summary = str(SubprocessError(cmd=cmd, status=status, stderr=stderr))
        return SanityError(test, summary=summary, python_version=python_version)

    if stdout:
        display.info(stdout.strip(), verbosity=3)

    if stderr:
        summary = 'Output on stderr from ansible-doc is considered an error.\n\n%s' % SubprocessError(cmd, stderr=stderr)
        return SanityError(test, summary=summary, python_version=python_version)

    return SanitySuccess(test)


def collect_code_smell_tests():
    """
    :rtype: tuple(SanityFunc)
    """
    with open('test/sanity/code-smell/skip.txt', 'r') as skip_fd:
        skip_tests = skip_fd.read().splitlines()

    paths = glob.glob('test/sanity/code-smell/*')
    paths = sorted(p for p in paths
                   if os.access(p, os.X_OK)
                   and os.path.isfile(p)
                   and os.path.basename(p) not in skip_tests)

    tests = tuple(SanityFunc(os.path.splitext(os.path.basename(p))[0], command_sanity_code_smell, script=p, intercept=False) for p in paths)

    return tests


def sanity_init():
    """Initialize full sanity test list (includes code-smell scripts determined at runtime)."""
    global SANITY_TESTS  # pylint: disable=locally-disabled, global-statement
    SANITY_TESTS = tuple(sorted(SANITY_TESTS + collect_code_smell_tests(), key=lambda k: k.name))


def sanity_get_tests():
    """
    :rtype: tuple(SanityFunc)
    """
    return SANITY_TESTS


class SanityResult(object):
    """Base class for sanity test results."""
    def __init__(self, test, python_version=None):
        """
        :type test: str
        :type python_version: str
        """
        self.test = test
        self.python_version = python_version

        try:
            import junit_xml
        except ImportError:
            junit_xml = None

        self.junit = junit_xml

    def write(self, args, changed_paths):
        """
        :type args: SanityConfig
        :type changed_paths: list[str] | None
        """
        self.write_console()

        if args.lint:
            self.write_lint()

        if args.junit:
            if self.junit:
                self.write_junit(args, changed_paths)
            else:
                display.warning('Skipping junit xml output because the `junit-xml` python package was not found.', unique=True)

    def write_console(self):
        """Write results to console."""
        pass

    def write_lint(self):
        """Write lint results to stdout."""
        pass

    def write_junit(self, args, changed_paths):
        """
        :type args: SanityConfig
        :type changed_paths: list[str] | None
        """
        pass

    def save_junit(self, args, test_case, properties=None):
        """
        :type args: SanityConfig
        :type test_case: junit_xml.TestCase
        :type properties: dict[str, str] | None
        :rtype: str | None
        """
        path = 'test/results/junit/ansible-test-%s' % self.test

        if self.python_version:
            path += '-python-%s' % self.python_version

        path += '.xml'

        test_suites = [
            self.junit.TestSuite(
                name='ansible-test sanity',
                test_cases=[test_case],
                timestamp=datetime.datetime.utcnow().replace(microsecond=0).isoformat(),
                properties=properties,
            ),
        ]

        report = self.junit.TestSuite.to_xml_string(test_suites=test_suites, prettyprint=True, encoding='utf-8')

        if args.explain:
            return

        with open(path, 'wb') as xml:
            xml.write(report.encode('utf-8', 'strict'))


class SanitySuccess(SanityResult):
    """Sanity test success."""
    def __init__(self, test, python_version=None):
        """
        :type test: str
        :type python_version: str
        """
        super(SanitySuccess, self).__init__(test, python_version)

    def write_junit(self, args, changed_paths):
        """
        :type args: SanityConfig
        :type changed_paths: list[str] | None
        """
        test_case = self.junit.TestCase(name=self.test)

        self.save_junit(args, test_case)


class SanitySkipped(SanityResult):
    """Sanity test skipped."""
    def __init__(self, test, python_version=None):
        """
        :type test: str
        :type python_version: str
        """
        super(SanitySkipped, self).__init__(test, python_version)

    def write_console(self):
        """Write results to console."""
        display.info('No tests applicable.', verbosity=1)

    def write_junit(self, args, changed_paths):
        """
        :type args: SanityConfig
        :type changed_paths: list[str] | None
        """
        test_case = self.junit.TestCase(name=self.test)
        test_case.add_skipped_info('No tests applicable.')

        self.save_junit(args, test_case)


class SanityError(SanityResult):
    """Sanity test error."""
    def __init__(self, test, python_version=None, messages=None, summary=None):
        """
        :type test: str
        :type python_version: str
        :type messages: list[SanityMessage]
        :type summary: str
        """
        super(SanityError, self).__init__(test, python_version)

        self.messages = messages
        self.summary = summary

    def write_console(self):
        """Write results to console."""
        if self.summary:
            display.error(self.summary)
        else:
            display.error('Found %d %s issue(s) which need to be resolved.' % (len(self.messages), self.test))

            for message in self.messages:
                display.error(message)

    def write_lint(self):
        """Write lint results to stdout."""
        if self.summary:
            command = self.format_command()
            message = 'The test `%s` failed. See stderr output for details.' % command
            path = 'test/runner/ansible-test'
            message = SanityMessage(message, path)
            print(message)
        else:
            for message in self.messages:
                print(message)

    def write_junit(self, args, changed_paths):
        """
        :type args: SanityConfig
        :type changed_paths: list[str] | None
        """
        confirmed = self.check_confirmed(changed_paths)
        output = self.format_block()

        test_case = self.junit.TestCase(name=self.test)
        test_case.add_error_info(output='\n%s\n' % output)

        properties = dict(
            confirmed=str(confirmed),
        )

        self.save_junit(args, test_case, properties)

    def check_confirmed(self, changed_paths):
        """
        :type changed_paths: list[str] | None
        :rtype: bool
        """
        if changed_paths is None:
            # changed paths not available
            return False

        if self.summary:
            # no paths to check
            return False

        paths = set(changed_paths)

        if all(m.path in paths for m in self.messages):
            # all paths in messages are changed paths
            return True

        # unrelated paths found in messages
        return False

    def format_command(self):
        """
        :rtype: str
        """
        command = 'ansible-test sanity %s' % self.test

        if self.python_version:
            command += ' --python %s' % self.python_version

        return command

    def format_block(self):
        """
        :rtype: str
        """
        command = self.format_command()

        if self.summary:
            block = self.summary
            reason = 'error'
        else:
            block = '\n'.join(str(m) for m in self.messages)
            reason = 'error' if len(self.messages) == 1 else 'errors'

        message = textwrap.dedent('''
        The test `%s` failed with the following %s:

        ```
        %s
        ```
        ''').strip() % (command, reason, block.strip())

        return message


class SanityMessage(object):
    """Single sanity test message for one file."""
    def __init__(self, message, path, line=0, column=0, level='error', code=None):
        """
        :type message: str
        :type path: str
        :type line: int
        :type column: int
        :type code: str | None
        """
        self.path = path
        self.line = line
        self.column = column
        self.level = level
        self.code = code
        self.message = message

    def __str__(self):
        if self.code:
            msg = '%s %s' % (self.code, self.message)
        else:
            msg = self.message

        return '%s:%s:%s: %s' % (self.path, self.line, self.column, msg)


class SanityTargets(object):
    """Sanity test target information."""
    def __init__(self, include, exclude, require):
        """
        :type include: list[str]
        :type exclude: list[str]
        :type require: list[str]
        """
        self.all = not include
        self.targets = tuple(sorted(walk_sanity_targets()))
        self.include = walk_internal_targets(self.targets, include, exclude, require)
        self.include_external, self.exclude_external = walk_external_targets(self.targets, include, exclude, require)


class SanityTest(object):
    """Sanity test base class."""
    def __init__(self, name):
        self.name = name


class SanityFunc(SanityTest):
    """Sanity test function information."""
    def __init__(self, name, func, intercept=True, script=None):
        """
        :type name: str
        :type func: (SanityConfig, SanityTargets) -> SanityResult
        :type intercept: bool
        :type script: str | None
        """
        super(SanityFunc, self).__init__(name)

        self.func = func
        self.intercept = intercept
        self.script = script


SANITY_TESTS = (
    SanityFunc('shellcheck', command_sanity_shellcheck, intercept=False),
    SanityFunc('pep8', command_sanity_pep8, intercept=False),
    SanityFunc('yamllint', command_sanity_yamllint, intercept=False),
    SanityFunc('validate-modules', command_sanity_validate_modules, intercept=False),
    SanityFunc('ansible-doc', command_sanity_ansible_doc),
)
