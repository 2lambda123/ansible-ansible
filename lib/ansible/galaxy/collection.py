# Copyright: (c) 2019, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import fnmatch
import json
import os
import shutil
import tarfile
import tempfile
import time
import uuid
import yaml

from contextlib import contextmanager
from distutils.version import LooseVersion
from hashlib import sha256
from io import BytesIO
from yaml.error import YAMLError

try:
    from urllib.parse import urlparse  # Python 3
except ImportError:
    from urlparse import urlparse  # Python 2

import ansible.constants as C
import ansible.module_utils.six.moves.urllib.error as urllib_error
from ansible.errors import AnsibleError
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.utils.display import Display
from ansible.utils.hashing import secure_hash, secure_hash_s

from ansible.module_utils.urls import open_url


display = Display()

MANIFEST_FORMAT = 1


class CollectionRequirement(object):

    _FILE_MAPPING = [('MANIFEST.json', 'manifest'), ('FILES.json', 'files')]

    def __init__(self, namespace, name, path, source, versions, requirement, parent=None, validate_certs=True,
                 metadata=None, files=None, skip=False):
        """
        Represents a collection requirement, the versions that are available to be installed as well as any
        dependencies the collection has.

        :param namespace: The collection namespace.
        :param name: The collection name.
        :param path: The path to the collection tarball if it has already been downloaded.
        :param source: The Galaxy server URL to download if the collection from Galaxy.
        :param versions: A list of versions of the collection that is available
        :param requirement: The version requirement string used to verify the list of versions fit the requirements.
        :param parent: The name of the parent the collection is a dependency of.
        :param validate_certs: Whether to validate the Galaxy server certificate.
        :param metadata: The collection metadata dict if it has already been retrieved.
        :param files: The files that exist inside the collection. This is based on the FILES.json file inside the
            collection artifact.
        :param skip: Whether to skip installing the collection, should be set if the collection is already installed
            and force is not set.
        """
        self.namespace = namespace
        self.name = name
        self.path = path
        self.source = source
        self.versions = set(versions)
        self.skip = skip
        self._validate_certs = validate_certs

        self._metadata = metadata
        self._files = files
        self._galaxy_info = None

        self.add_requirement(parent, requirement)

    def __str__(self):
        return "%s.%s" % (self.namespace, self.name)

    @property
    def latest_version(self):
        versions = [v for v in self.versions if v != '*']
        if versions:
            sorted(versions, key=LooseVersion)
            return versions[-1]
        else:
            return '*'

    @property
    def dependencies(self):
        if self._metadata:
            return self._metadata['dependencies']
        elif len(self.versions) > 1:
            return None

        collection_url = _urljoin(*[self.source, 'api', 'v2', 'collections', self.namespace, self.name, 'versions',
                                    self.latest_version])
        details = json.load(open_url(collection_url, validate_certs=self._validate_certs))
        self._galaxy_info = details
        self._metadata = details['metadata']

        return self._metadata['dependencies']

    def add_requirement(self, parent, requirement):
        new_versions = set([v for v in self.versions if self._meets_requirements(v, requirement)])
        if len(new_versions) == 0:
            if self.skip:
                force_flag = '--force-with-deps' if parent else '--force'
                msg = "Cannot meet requirement %s for dependency %s as it is already installed. Use %s to overwrite" \
                      % (requirement, str(self), force_flag)
            elif parent is None:
                msg = "Cannot meet requirement %s for dependency %s" % (requirement, str(self))
            else:
                msg = "Cannot meet dependency requirement '%s:%s' for collection %s" % (str(self), requirement, parent)

            collection_source = self.path or self.source
            raise AnsibleError("%s from source '%s'. Available versions: %s" % (msg, collection_source,
                                                                                ", ".join(self.versions)))

        self.versions = new_versions

    def install(self, path, temp_path):
        if self.skip:
            display.display("Skipping '%s' as it is already installed" % str(self))
            return

        # Install if it is not
        collection_path = os.path.join(path, self.namespace, self.name)
        display.display("Installing '%s:%s' to '%s'" % (str(self), self.latest_version,
                                                        collection_path))

        if self.path is None:
            download_url = self._galaxy_info['download_url']
            artifact_hash = self._galaxy_info['artifact']['sha256']
            self.path = _download_file(download_url, temp_path, artifact_hash, self._validate_certs)

        if os.path.exists(collection_path):
            shutil.rmtree(collection_path)
        os.makedirs(collection_path)

        with tarfile.open(self.path, mode='r') as collection_tar:
            files_member_obj = collection_tar.getmember('FILES.json')
            with collection_tar.extractfile(files_member_obj) as files_obj:
                files = json.load(files_obj)

            _extract_tar_file(collection_tar, 'MANIFEST.json', collection_path, temp_path)
            _extract_tar_file(collection_tar, 'FILES.json', collection_path, temp_path)

            for file_info in files['files']:
                file_name = file_info['name']
                if file_name == '.':
                    continue

                if file_info['ftype'] == 'file':
                    _extract_tar_file(collection_tar, file_name, collection_path, temp_path,
                                      expected_hash=file_info['chksum_sha256'])
                else:
                    os.makedirs(os.path.join(collection_path, file_name))

    def set_latest_version(self):
        self.versions = {self.latest_version}

    def _meets_requirements(self, version, requirements):
        """
        Supports version identifiers can be '==', '!=', '>', '>=', '<', '<=', '*'. Each requirement is delimited by ','
        """
        for req in requirements.split(','):
            if req.startswith('!='):
                if version == req[2:]:
                    break
            elif req.startswith('>'):
                if req[1] == '=' and LooseVersion(version) < LooseVersion(req[2:]):
                    break
                elif req[1] != '=' and LooseVersion(version) <= LooseVersion(req[2:]):
                    break
            elif req.startswith('<'):
                if req[1] == '=' and LooseVersion(version) > LooseVersion(req[2:]):
                    break
                elif req[1] != '=' and LooseVersion(version) >= LooseVersion(req[2:]):
                    break
            elif req != '*':
                # Either prefixed with '==' or just the version, we want to match the exact version.
                req_version = req[2:] if req.startswith('==') else req
                if version != req_version:
                    break
        else:
            return True

        # The loop was broken early, it does not meet all the requirements
        return False

    @staticmethod
    def from_tar(path, validate_certs, parent=None):
        if not tarfile.is_tarfile(path):
            raise AnsibleError("Collection artifact at '%s' is not a valid tar file." % path)

        info = {}
        with tarfile.open(path, mode='r') as collection_tar:
            for member_name, property_name in CollectionRequirement._FILE_MAPPING:
                try:
                    member = collection_tar.getmember(member_name)
                except KeyError:
                    raise AnsibleError("Collection at '%s' does not contain the required file %s."
                                       % (path, member_name))

                with collection_tar.extractfile(member) as member_obj:
                    try:
                        info[property_name] = json.load(member_obj)
                    except ValueError:
                        raise AnsibleError("Collection tar file %s is not a valid json string." % member_name)

        meta = info['manifest']['collection_info']
        files = info['files']['files']

        namespace = meta['namespace']
        name = meta['name']
        version = meta['version']

        return CollectionRequirement(namespace, name, path, None, [version], version, parent=parent,
                                     validate_certs=validate_certs, metadata=meta, files=files)

    @staticmethod
    def from_path(path, validate_certs, parent=None):
        info = {}
        for file_name, property_name in CollectionRequirement._FILE_MAPPING:
            file_path = os.path.join(path, file_name)
            if os.path.exists(file_path):
                with open(file_path, 'rb') as file_obj:
                    try:
                        info[property_name] = json.load(file_obj)
                    except ValueError:
                        raise AnsibleError("Collection file at '%s' is not a valid json string." % file_path)

        if 'manifest' in info:
            meta = info['manifest']['collection_info']
        else:
            parent_dir, name = os.path.split(path)
            namespace = os.path.split(parent_dir)[1]
            version = '*'
            meta = {
                'namespace': namespace,
                'name': name,
                'version': version,
                'dependencies': {},
            }

        namespace = meta['namespace']
        name = meta['name']
        version = meta['version']

        files = info.get('files', {}).get('files', {})

        return CollectionRequirement(namespace, name, path, None, [version], version, parent=parent,
                                     validate_certs=validate_certs, metadata=meta, files=files, skip=True)

    @staticmethod
    def from_name(collection, servers, requirement, validate_certs, parent=None):
        namespace, name = collection.split('.', 1)
        galaxy_info = None
        galaxy_meta = None

        for server in servers:
            collection_url_paths = [server, 'api', 'v2', 'collections', namespace, name, 'versions']

            is_single = False
            if not (requirement == '*' or requirement.startswith('<') or requirement.startswith('>')):
                collection_url_paths.append(requirement)
                is_single = True

            collection_uri = _urljoin(*collection_url_paths)
            try:
                resp = json.load(open_url(collection_uri, validate_certs=validate_certs))
            except urllib_error.HTTPError as err:
                if err.code == 404:
                    continue
                raise

            if is_single:
                galaxy_info = resp
                galaxy_meta = resp['metadata']
                versions = [resp['version']]
            else:
                versions = []
                while True:
                    versions += [v['version'] for v in resp['results']]
                    if resp['next'] is None:
                        break
                    resp = json.load(open_url(resp['next'], validate_certs=validate_certs))

            break
        else:
            raise AnsibleError("Failed to find collection %s:%s" % (collection, requirement))

        req = CollectionRequirement(namespace, name, None, server, versions, requirement, parent=parent,
                                    validate_certs=validate_certs, metadata=galaxy_meta)
        req._galaxy_info = galaxy_info
        return req


def build_collection(collection_path, output_path, force):
    """
    Creates the Ansible collection artifact in a .tar.gz file.

    :param collection_path: The path to the collection to build. This should be the directory that contains the
        galaxy.yml file.
    :param output_path: The path to create the collection build artifact. This should be a directory.
    :param force: Whether to overwrite an existing collection build artifact or fail.
    :return: The path to the collection build artifact.
    """
    galaxy_path = os.path.join(collection_path, 'galaxy.yml')
    if not os.path.exists(galaxy_path):
        raise AnsibleError("The collection galaxy.yml path '%s' does not exist." % galaxy_path)

    collection_meta = _get_galaxy_yml(galaxy_path)
    file_manifest = _build_files_manifest(collection_path)
    collection_manifest = _build_manifest(**collection_meta)

    collection_output = os.path.join(output_path, "%s-%s-%s.tar.gz" % (collection_meta['namespace'],
                                                                       collection_meta['name'],
                                                                       collection_meta['version']))

    if os.path.exists(collection_output):
        if os.path.isdir(collection_output):
            raise AnsibleError("The output collection artifact '%s' already exists, "
                               "but is a directory - aborting" % collection_output)
        elif not force:
            raise AnsibleError("The file '%s' already exists. You can use --force to re-create "
                               "the collection artifact." % collection_output)

    _build_collection_tar(collection_path, collection_output, collection_manifest, file_manifest)


def publish_collection(collection_path, server, key, ignore_certs, wait):
    """
    Publish an Ansible collection tarball into an Ansible Galaxy server.

    :param collection_path: The path to the collection tarball to publish.
    :param server: A native string of the Ansible Galaxy server to publish to.
    :param key: The API key to use for authorization.
    :param ignore_certs: Whether to ignore certificate validation when interacting with the server.
    """
    if not os.path.exists(collection_path):
        raise AnsibleError("The collection path specified '%s' does not exist." % collection_path)
    elif not tarfile.is_tarfile(collection_path):
        raise AnsibleError("The collection path specified '%s' is not a tarball, use 'ansible-galaxy collection "
                           "build' to create a proper release artifact." % collection_path)

    display.display("Publishing collection artifact '%s' to %s" % (to_text(collection_path), server))

    url = _urljoin(server, 'api', 'v2', 'collections')

    data, content_type = _get_mime_data(collection_path)
    headers = {
        'Content-type': content_type,
        'Content-length': len(data),
    }
    if key:
        headers['Authorization'] = "Token %s" % key
    validate_certs = not ignore_certs

    try:
        resp = json.load(open_url(url, data=data, headers=headers, method='POST', validate_certs=validate_certs))
    except urllib_error.HTTPError as err:
        try:
            err_info = json.load(err)
        except (AttributeError, ValueError):
            err_info = {}

        code = err_info.get('code', 'Unknown')
        message = err_info.get('message', 'Unknown error returned by Galaxy server.')

        raise AnsibleError("Error when publishing collection (HTTP Code: %d, Message: %s Code: %s)"
                           % (err.code, message, code))

    display.vvv("Collection has been pushed to the Galaxy server %s" % server)
    import_uri = resp['task']
    if wait:
        _wait_import(import_uri, key, validate_certs)
        display.display("Collection has been successfully published to the Galaxy server")
    else:
        display.display("Collection has been pushed to the Galaxy server, not waiting until import has completed "
                        "due to --no-wait being set. Import task results can be found at %s" % import_uri)


def install_collections(collections, output_path, servers, validate_certs, ignore_errors, no_deps, force, force_deps):
    """
    Install Ansible collections to the path specified.

    :param collections: The collections to install, should be a list of tuples with (name, requirement, galaxy server).
    :param output_path: The path to install the collections to.
    :param servers: A list of Galaxy servers to query when searching for a collection.
    :param validate_certs: Whether to validate the Galaxy server certificates.
    :param ignore_errors: Whether to ignore any errors when installing the collection.
    :param no_deps: Ignore any collection dependencies and only install the base requirements.
    :param force: Re-install a collection if it has already been installed.
    :param force_deps: Re-install a collection as well as its dependencies if they have already been installed.
    """
    existing_collections = _find_existing_collections(output_path)

    with _tempdir() as temp_path:
        dependency_map = _build_dependency_map(collections, existing_collections, temp_path, servers, validate_certs,
                                               force, force_deps, no_deps)

        for collection in dependency_map.values():
            try:
                collection.install(output_path, temp_path)
            except AnsibleError as err:
                if ignore_errors:
                    display.warning("Failed to install collection %s but skipping due to --ignore-errors being set. "
                                    "Error: %s" % (str(collection), to_text(err)))
                else:
                    raise


def parse_collections_requirements_file(requirements_file):
    """
    Parses an Ansible requirement.yml file and returns all the collections defined in it. This value ca be used with
    install_collection(). The requirements file is in the form;

        ---
        collections:
        - namespace.collection
        - name: namespace.collection
          version: version identifier, multiple identifiers are separated by ','
          source: the URL or prededefined source name in ~/.ansible_galaxy to pull the collection from

    :param requirements_file: The path to the requirements file.
    :return: A list of tuples (name, version, source).
    """
    collection_info = []

    requirements_file = os.path.expanduser(os.path.expandvars(requirements_file))
    if not os.path.exists(requirements_file):
        raise AnsibleError("The requirements file '%s' does not exist." % requirements_file)

    display.vvv("Reading collection requirement file at '%s'" % requirements_file)
    with open(requirements_file, 'rb') as req_obj:
        requirements = yaml.safe_load(req_obj)

    if not isinstance(requirements, dict) or 'collections' not in requirements:
        raise AnsibleError("Expecting collections requirements file to be a dict with the key "
                           "collections that contains a list of collections to install.")

    for collection_req in requirements['collections']:
        if isinstance(collection_req, dict):
            req_name = collection_req.get('name', None)
            if req_name is None:
                raise AnsibleError("Collections requirement entry should contain the key name.")

            req_version = collection_req.get('version', None)
            req_source = collection_req.get('source', None)

            collection_info.append((req_name, req_version, req_source))
        else:
            collection_info.append((collection_req, '*', None))

    return collection_info


@contextmanager
def _tempdir():
    temp_path = tempfile.mkdtemp(dir=C.DEFAULT_LOCAL_TMP)
    yield temp_path
    shutil.rmtree(temp_path)


def _get_galaxy_yml(galaxy_yml_path):
    mandatory_keys = frozenset(['namespace', 'name', 'version', 'authors', 'readme'])
    optional_strings = ('description', 'repository', 'documentation', 'homepage', 'issues', 'license_file')
    optional_lists = ('license', 'tags', 'authors')  # authors isn't optional but this will ensure it is list
    optional_dicts = ('dependencies',)
    all_keys = frozenset(list(mandatory_keys) + list(optional_strings) + list(optional_lists) + list(optional_dicts))

    try:
        with open(to_bytes(galaxy_yml_path), 'rb') as g_yaml:
            galaxy_yml = yaml.safe_load(g_yaml)
    except YAMLError as err:
        raise AnsibleError("Failed to parse the galaxy.yml at '%s' with the following error:\n%s"
                           % (to_native(galaxy_yml_path), to_native(err)))

    set_keys = set(galaxy_yml.keys())
    missing_keys = mandatory_keys.difference(set_keys)
    if len(missing_keys) > 0:
        raise AnsibleError("The collection galaxy.yml at '%s' is missing the following mandatory keys: %s"
                           % (to_native(galaxy_yml_path), ", ".join(sorted(missing_keys))))

    extra_keys = set_keys.difference(all_keys)
    if len(extra_keys) > 0:
        display.warning("Found unknown keys in collection galaxy.yml at '%s': %s"
                        % (to_native(galaxy_yml_path), ", ".join(extra_keys)))

    # Add the defaults if they have not been set
    for optional_string in optional_strings:
        if optional_string not in galaxy_yml:
            galaxy_yml[optional_string] = None

    for optional_list in optional_lists:
        list_val = galaxy_yml.get(optional_list, None)

        if list_val is None:
            galaxy_yml[optional_list] = []
        elif not isinstance(list_val, list):
            galaxy_yml[optional_list] = [list_val]

    for optional_dict in optional_dicts:
        if optional_dict not in galaxy_yml:
            galaxy_yml[optional_dict] = {}

    # license is a builtin var in Python, to avoid confusion we just rename it to license_ids
    galaxy_yml['license_ids'] = galaxy_yml['license']
    del galaxy_yml['license']

    return galaxy_yml


def _build_files_manifest(collection_path):
    ignore_files = frozenset(['*.pyc', '*.retry'])
    ignore_dirs = frozenset(['CVS', '.bzr', '.hg', '.git', '.svn', '__pycache__', '.tox'])

    entry_template = {
        'name': None,
        'ftype': None,
        'chksum_type': None,
        'chksum_sha256': None,
        'format': MANIFEST_FORMAT
    }
    manifest = {
        'files': [
            {
                'name': '.',
                'ftype': 'dir',
                'chksum_type': None,
                'chksum_sha256': None,
                'format': MANIFEST_FORMAT,
            },
        ],
        'format': MANIFEST_FORMAT,
    }

    def _walk(path, top_level_dir):
        for item in os.listdir(path):
            abs_path = os.path.join(path, item)
            rel_base_dir = '' if path == top_level_dir else path[len(top_level_dir) + 1:]
            rel_path = os.path.join(rel_base_dir, item)

            if os.path.isdir(abs_path):
                if item in ignore_dirs:
                    display.vvv("Skipping '%s' for collection build" % to_text(abs_path))
                    continue

                if os.path.islink(abs_path):
                    link_target = os.path.realpath(abs_path)

                    if not link_target.startswith(top_level_dir):
                        display.warning("Skipping '%s' as it is a symbolic link to a directory outside the collection"
                                        % to_text(abs_path))
                        continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'dir'

                manifest['files'].append(manifest_entry)

                _walk(abs_path, top_level_dir)
            else:
                if item == 'galaxy.yml':
                    continue
                elif any(fnmatch.fnmatch(item, pattern) for pattern in ignore_files):
                    display.vvv("Skipping '%s' for collection build" % to_text(abs_path))
                    continue

                manifest_entry = entry_template.copy()
                manifest_entry['name'] = rel_path
                manifest_entry['ftype'] = 'file'
                manifest_entry['chksum_type'] = 'sha256'
                manifest_entry['chksum_sha256'] = secure_hash(abs_path, hash_func=sha256)

                manifest['files'].append(manifest_entry)

    _walk(collection_path, collection_path)

    return manifest


def _build_manifest(namespace, name, version, authors, readme, tags, description, license_ids, license_file,
                    dependencies, repository, documentation, homepage, issues, **kwargs):

    manifest = {
        'collection_info': {
            'namespace': namespace,
            'name': name,
            'version': version,
            'authors': authors,
            'readme': readme,
            'tags': tags,
            'description': description,
            'license': license_ids,
            'license_file': license_file,
            'dependencies': dependencies,
            'repository': repository,
            'documentation': documentation,
            'homepage': homepage,
            'issues': issues,
        },
        'file_manifest_file': {
            'name': 'FILES.json',
            'ftype': 'file',
            'chksum_type': 'sha256',
            'chksum_sha256': None,  # Filled out in _build_collection_tar
            'format': MANIFEST_FORMAT
        },
        'format': MANIFEST_FORMAT,
    }

    return manifest


def _build_collection_tar(collection_path, tar_path, collection_manifest, file_manifest):
    files_manifest_json = to_bytes(json.dumps(file_manifest, indent=True), errors='surrogate_or_strict')
    collection_manifest['file_manifest_file']['chksum_sha256'] = secure_hash_s(files_manifest_json, hash_func=sha256)
    collection_manifest_json = to_bytes(json.dumps(collection_manifest, indent=True), errors='surrogate_or_strict')

    with _tempdir() as temp_path:
        tar_filepath = os.path.join(temp_path, os.path.basename(tar_path))

        with tarfile.open(tar_filepath, mode='w:gz') as tar_file:
            # Add the MANIFEST.json and FILES.json file to the archive
            for name, b in [('MANIFEST.json', collection_manifest_json), ('FILES.json', files_manifest_json)]:
                b_io = BytesIO(b)
                tar_info = tarfile.TarInfo(name)
                tar_info.size = len(b)
                tar_info.mtime = time.time()
                tar_info.mode = 0o0644
                tar_file.addfile(tarinfo=tar_info, fileobj=b_io)

            for file_info in file_manifest['files']:
                if file_info['name'] == '.':
                    continue

                filename = to_text(file_info['name'], errors='surrogate_or_strict')
                src_path = os.path.join(to_text(collection_path, errors='surrogate_or_strict'), filename)

                if os.path.islink(src_path) and os.path.isfile(src_path):
                    src_path = os.path.realpath(src_path)

                def reset_stat(tarinfo):
                    if tarinfo.issym() or tarinfo.islnk():
                        return None

                    tarinfo.mode = 0o0755 if tarinfo.isdir() else 0o0644
                    tarinfo.uid = tarinfo.gid = 0
                    tarinfo.uname = tarinfo.gname = ''
                    return tarinfo

                tar_file.add(src_path, arcname=filename, recursive=False, filter=reset_stat)

        shutil.copy(tar_filepath, tar_path)
        collection_name = "%s.%s" % (collection_manifest['collection_info']['namespace'],
                                     collection_manifest['collection_info']['name'])
        display.display('Created collection for %s at %s' % (collection_name, to_text(tar_path)))


def _get_mime_data(collection_path):
    with open(collection_path, 'rb') as collection_tar:
        data = collection_tar.read()

    boundary = '--------------------------%s' % uuid.uuid4().hex
    file_name = to_bytes(os.path.basename(collection_path), errors='surrogate_or_strict')
    part_boundary = b"--" + to_bytes(boundary, errors='surrogate_or_strict')

    form = [
        part_boundary,
        b"Content-Disposition: form-data; name=\"sha256\"",
        to_bytes(secure_hash_s(data), errors='surrogate_or_strict'),
        part_boundary,
        b"Content-Disposition: file; name=\"file\"; filename=\"%s\"" % file_name,
        b"Content-Type: application/octet-stream",
        b"",
        data,
        b"%s--" % part_boundary,
    ]

    content_type = 'multipart/form-data; boundary=%s' % boundary

    return b"\r\n".join(form), content_type


def _wait_import(task_url, key, validate_certs):
    headers = {}
    if key:
        headers['Authorization'] = "Token %s" % key

    wait = 2
    display.vvv('Waiting until galaxy import task %s has completed' % task_url)

    while True:
        resp = json.load(open_url(task_url, headers=headers, method='GET', validate_certs=validate_certs))

        if resp.get('finished_at', None):
            break

        status = resp.get('status', 'waiting')
        display.vvv('Galaxy import process has a status of %s, wait %d seconds before trying again' % (status, wait))
        time.sleep(wait)

    for message in resp.get('messages', []):
        level = message['level']
        if level == 'error':
            display.error("Galaxy import error message: %s" % message['message'])
        elif level == 'warning':
            display.warning("Galaxy import warning message: %s" % message['message'])
        else:
            display.vvv("Galaxy import message: %s - %s" % (level, message['message']))

    if resp['state'] == 'failed':
        code = resp['error'].get('code', 'UNKNOWN')
        description = resp['error'].get('description', "Unknown error, see %s for more details" % task_url)
        raise AnsibleError("Galaxy import process failed: %s (Code: %s)" % (description, code))


def _find_existing_collections(path):
    collections = []

    for namespace in os.listdir(path):
        namespace_path = os.path.join(path, namespace)
        if os.path.isfile(namespace_path):
            continue

        for collection in os.listdir(namespace_path):
            collection_path = os.path.join(namespace_path, collection)
            if os.path.isdir(collection_path):
                req = CollectionRequirement.from_path(collection_path, True)
                display.vvv("Found installed collection %s:%s at '%s'" % (str(req), req.latest_version,
                                                                          collection_path))
                collections.append(req)

    return collections


def _build_dependency_map(collections, existing_collections, temp_path, servers, validate_certs, force, force_deps,
                          no_deps):
    dependency_map = {}

    # First build the dependency map on the actual requirements
    for name, version, source in collections:
        _get_collection_info(dependency_map, existing_collections, name, version, source, temp_path, servers,
                             validate_certs, (force or force_deps))

    # Now parse the dependency requirements if no_deps was not set
    if not no_deps:
        checked_parents = set([str(c) for c in dependency_map.values() if c.skip])

        while len(dependency_map) != len(checked_parents):
            while True:
                parents_to_check = set(dependency_map.keys()).difference(checked_parents)

                deps_exhausted = True
                for parent in parents_to_check:
                    parent_info = dependency_map[parent]

                    if parent_info.dependencies:
                        deps_exhausted = False
                        for dep_name, dep_requirement in parent_info.dependencies.items():
                            _get_collection_info(dependency_map, existing_collections, dep_name, dep_requirement,
                                                 parent_info.source, temp_path, servers, validate_certs, force_deps,
                                                 parent=parent)

                        checked_parents.add(parent)

                # No extra dependencies were resolved, exit loop
                if deps_exhausted:
                    break

            # Now we have resolved the deps to our best extent, now select the latest version for collections with
            # multiple versions found and go from there
            deps_not_checked = set(dependency_map.keys()).difference(checked_parents)
            for collection in deps_not_checked:
                dependency_map[collection].set_latest_version()
                if len(dependency_map[collection].dependencies) == 0:
                    checked_parents.add(collection)

    return dependency_map


def _get_collection_info(dep_map, existing_collections, collection, requirement, source, temp_path, server_list,
                         validate_certs, force, parent=None):
    dep_msg = ""
    if parent:
        dep_msg = " - as dependency of %s" % parent
    display.vvv("Processing requirement collection '%s'%s" % (collection, dep_msg))

    tar_path = None
    if os.path.isfile(collection):
        display.vvvv("Collection requirement '%s' is a tar artifact" % collection)
        tar_path = collection
    elif urlparse(collection).scheme:
        display.vvvv("Collection requirement '%s' is a URL to a tar artifact" % collection)
        tar_path = _download_file(collection, temp_path, None, validate_certs)

    if tar_path:
        req = CollectionRequirement.from_tar(tar_path, validate_certs, parent=parent)

        collection_name = str(req)
        if collection_name in dep_map:
            collection_info = dep_map[collection_name]
            collection_info.add_requirement(None, req.latest_version)
        else:
            collection_info = req
    else:
        display.vvvv("Collection requirement '%s' is the name of a collection" % collection)
        if collection in dep_map:
            collection_info = dep_map[collection]
            collection_info.add_requirement(parent, requirement)
        else:
            servers = [source] if source else server_list
            collection_info = CollectionRequirement.from_name(collection, servers, requirement, validate_certs,
                                                              parent=parent)

    existing = [c for c in existing_collections if str(c) == str(collection_info)]
    if existing and not force:
        collection_info = existing[0]

    dep_map[str(collection_info)] = collection_info


def _urljoin(*args):
    return "/".join(map(lambda x: to_text(x).rstrip('/'), args)) + "/"


def _download_file(url, path, expected_hash, validate_certs):
    bufsize = 65536
    digest = sha256()

    file_name, file_ext = os.path.splitext(to_text(url.rsplit('/', 1)[1]))
    file_path = tempfile.NamedTemporaryFile(dir=path, prefix=file_name, suffix=file_ext, delete=False).name

    display.vvv("Downloading %s to %s" % (url, path))
    resp = open_url(url, validate_certs=validate_certs)

    with open(file_path, 'wb') as download_file:
        data = resp.read(bufsize)
        while data:
            digest.update(data)
            download_file.write(data)
            data = resp.read(bufsize)

    if expected_hash:
        actual_hash = digest.hexdigest()
        display.vvvv("Validating downloaded file hash %s with expected hash %s" % (actual_hash, expected_hash))
        if expected_hash != actual_hash:
            raise AnsibleError("Mismatch artifact hash with downloaded file")

    return file_path


def _extract_tar_file(tar, filename, dest, temp_path, expected_hash=None):
    try:
        member = tar.getmember(filename)
    except KeyError:
        raise AnsibleError("Collection tar at '%s' does not contain the expected file %s." % (tar.name, filename))

    with tempfile.NamedTemporaryFile(dir=temp_path, delete=False) as tmpfile:
        bufsize = 65536
        sha256_digest = sha256()
        with tar.extractfile(member) as tar_obj:
            data = tar_obj.read(bufsize)
            while data:
                tmpfile.write(data)
                tmpfile.flush()
                sha256_digest.update(data)
                data = tar_obj.read(bufsize)

        actual_hash = sha256_digest.hexdigest()

        if expected_hash and actual_hash != expected_hash:
            raise AnsibleError("Checksum mismatch for '%s' inside collection at '%s'"
                               % (filename, tar.name))

        dest_filepath = os.path.join(dest, filename)
        parent_dir = os.path.split(dest_filepath)[0]
        if not os.path.exists(parent_dir):
            # Seems like Galaxy does not validate if all file entries have a corresponding dir ftype entry. This check
            # makes sure we create the parent directory even if it wasn't set in the metadata.
            os.makedirs(parent_dir)

        os.rename(tmpfile.name, dest_filepath)
