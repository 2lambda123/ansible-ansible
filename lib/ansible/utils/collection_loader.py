# (c) 2019 Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import os.path
import pkgutil
import re
import sys

from types import ModuleType

from ansible import constants as C
from ansible.module_utils._text import to_bytes, to_native, to_text
from ansible.module_utils.six import iteritems, string_types, with_metaclass
from ansible.utils.singleton import Singleton

# HACK: keep Python 2.6 controller tests happy in CI until they're properly split
try:
    from importlib import import_module
except ImportError:
    import_module = __import__

_SYNTHETIC_PACKAGES = {
    'ansible_collections.ansible': dict(type='pkg_only'),
    'ansible_collections.ansible.builtin': dict(type='pkg_only'),
    'ansible_collections.ansible.builtin.plugins': dict(type='map', map='ansible.plugins'),
    'ansible_collections.ansible.builtin.plugins.module_utils': dict(type='map', map='ansible.module_utils', graft=True),
    'ansible_collections.ansible.builtin.plugins.modules': dict(type='flatmap', flatmap='ansible.modules', graft=True),
}


# FIXME: exception handling/error logging
class AnsibleCollectionLoader(with_metaclass(Singleton, object)):
    def __init__(self):
        self._n_configured_paths = C.config.get_config_value('COLLECTIONS_PATHS')

        if isinstance(self._n_configured_paths, string_types):
            self._n_configured_paths = [self._n_configured_paths]
        elif self._n_configured_paths is None:
            self._n_configured_paths = []

        # expand any placeholders in configured paths
        self._n_configured_paths = [to_native(os.path.expanduser(p), errors='surrogate_or_strict') for p in self._n_configured_paths]

        self._n_playbook_paths = []
        # pre-inject grafted package maps so we can force them to use the right loader instead of potentially delegating to a "normal" loader
        for syn_pkg_def in (p for p in iteritems(_SYNTHETIC_PACKAGES) if p[1].get('graft')):
            pkg_name = syn_pkg_def[0]
            pkg_def = syn_pkg_def[1]

            newmod = ModuleType(pkg_name)
            newmod.__package__ = pkg_name
            newmod.__file__ = '<ansible_synthetic_collection_package>'
            pkg_type = pkg_def.get('type')

            # TODO: need to rethink map style so we can just delegate all the loading

            if pkg_type == 'flatmap':
                newmod.__loader__ = AnsibleFlatMapLoader(import_module(pkg_def['flatmap']))
            newmod.__path__ = []

            sys.modules[pkg_name] = newmod

    @property
    def n_collection_paths(self):
        return self._n_playbook_paths + self._n_configured_paths

    def set_playbook_paths(self, b_playbook_paths):
        if isinstance(b_playbook_paths, string_types):
            b_playbook_paths = [b_playbook_paths]

        # track visited paths; we have to preserve the dir order as-passed in case there are duplicate collections (first one wins)
        added_paths = set()

        # de-dupe and ensure the paths are native strings (Python seems to do this for package paths etc, so assume it's safe)
        self._n_playbook_paths = [os.path.join(to_native(p), 'collections') for p in b_playbook_paths if not (p in added_paths or added_paths.add(p))]
        # FIXME: only allow setting this once, or handle any necessary cache/package path invalidations internally?

    def find_module(self, fullname, path=None):
        # this loader is only concerned with items under the Ansible Collections namespace hierarchy, ignore others
        if fullname.startswith('ansible_collections.') or fullname == 'ansible_collections':
            return self

        return None

    def load_module(self, fullname):
        if sys.modules.get(fullname):
            return sys.modules[fullname]

        # this loader implements key functionality for Ansible collections
        # * implicit distributed namespace packages for the root Ansible namespace (no pkgutil.extend_path hackery reqd)
        # * implicit package support for Python 2.7 (no need for __init__.py in collections, except to use standard Py2.7 tooling)
        # * preventing controller-side code injection during collection loading
        # * (default loader would execute arbitrary package code from all __init__.py's)

        parent_pkg_name = '.'.join(fullname.split('.')[:-1])

        parent_pkg = sys.modules.get(parent_pkg_name)

        if parent_pkg_name and not parent_pkg:
            raise ImportError('parent package {0} not found'.format(parent_pkg_name))

        # are we at or below the collection level? eg a.mynamespace.mycollection.something.else
        # if so, we don't want distributed namespace behavior; first mynamespace.mycollection on the path is where
        # we'll load everything from (ie, don't fall back to another mynamespace.mycollection lower on the path)
        sub_collection = fullname.count('.') > 1

        synpkg_def = _SYNTHETIC_PACKAGES.get(fullname)
        synpkg_remainder = ''

        if not synpkg_def:
            synpkg_def = _SYNTHETIC_PACKAGES.get(parent_pkg_name)
            synpkg_remainder = '.' + fullname.rpartition('.')[2]

        # FIXME: collapse as much of this back to on-demand as possible (maybe stub packages that get replaced when actually loaded?)
        if synpkg_def:
            pkg_type = synpkg_def.get('type')
            if not pkg_type:
                raise KeyError('invalid synthetic package type (no package "type" specified)')
            if pkg_type == 'map':
                map_package = synpkg_def.get('map')

                if not map_package:
                    raise KeyError('invalid synthetic map package definition (no target "map" defined)')
                mod = import_module(map_package + synpkg_remainder)

                sys.modules[fullname] = mod

                return mod
            elif pkg_type == 'flatmap':
                raise NotImplementedError()
            elif pkg_type == 'pkg_only':
                newmod = ModuleType(fullname)
                newmod.__package__ = fullname
                newmod.__file__ = '<ansible_synthetic_collection_package>'
                newmod.__loader__ = self
                newmod.__path__ = []

                sys.modules[fullname] = newmod

                return newmod

        if not parent_pkg:  # top-level package, look for NS subpackages on all collection paths
            package_paths = [self._extend_path_with_ns(p, fullname) for p in self.n_collection_paths]
        else:  # subpackage; search in all subpaths (we'll limit later inside a collection)
            package_paths = [self._extend_path_with_ns(p, fullname) for p in parent_pkg.__path__]

        for candidate_child_path in package_paths:
            code_object = None
            is_package = True
            location = None
            # check for implicit sub-package first
            if os.path.isdir(candidate_child_path):
                # Py3.x implicit namespace packages don't have a file location, so they don't support get_data
                # (which assumes the parent dir or that the loader has an internal mapping); so we have to provide
                # a bogus leaf file on the __file__ attribute for pkgutil.get_data to strip off
                location = os.path.join(candidate_child_path, '__synthetic__')
            else:
                for source_path in [os.path.join(candidate_child_path, '__init__.py'),
                                    candidate_child_path + '.py']:
                    if not os.path.isfile(source_path):
                        continue

                    with open(source_path, 'rb') as fd:
                        source = fd.read()

                    code_object = compile(source=source, filename=source_path, mode='exec', flags=0, dont_inherit=True)
                    location = source_path
                    is_package = source_path.endswith('__init__.py')
                    break

                if not location:
                    continue

            newmod = ModuleType(fullname)
            newmod.__file__ = location
            newmod.__loader__ = self

            if is_package:
                if sub_collection:  # we never want to search multiple instances of the same collection; use first found
                    newmod.__path__ = [candidate_child_path]
                else:
                    newmod.__path__ = package_paths

                newmod.__package__ = fullname
            else:
                newmod.__package__ = parent_pkg_name

            sys.modules[fullname] = newmod

            if code_object:
                # FIXME: decide cases where we don't actually want to exec the code?
                exec(code_object, newmod.__dict__)

            return newmod

        # FIXME: need to handle the "no dirs present" case for at least the root and synthetic internal collections like ansible.builtin

        raise ImportError('module {0} not found'.format(fullname))

    @staticmethod
    def _extend_path_with_ns(path, ns):
        ns_path_add = ns.rsplit('.', 1)[-1]

        return os.path.join(path, ns_path_add)

    def get_data(self, filename):
        with open(filename, 'rb') as fd:
            return fd.read()


class AnsibleFlatMapLoader(object):
    _extension_blacklist = ['.pyc', '.pyo']

    def __init__(self, root_package):
        self._root_package = root_package
        self._dirtree = None

    def _init_dirtree(self):
        # FIXME: thread safety
        root_path = os.path.dirname(self._root_package.__file__)
        flat_files = []
        # FIXME: make this a dict of filename->dir for faster direct lookup?
        # FIXME: deal with _ prefixed deprecated files (or require another method for collections?)
        # FIXME: fix overloaded filenames (eg, rename Windows setup to win_setup)
        for root, dirs, files in os.walk(root_path):
            # add all files in this dir that don't have a blacklisted extension
            flat_files.extend(((root, f) for f in files if not any((f.endswith(ext) for ext in self._extension_blacklist))))
        self._dirtree = flat_files

    def find_file(self, filename):
        # FIXME: thread safety
        if not self._dirtree:
            self._init_dirtree()

        if '.' not in filename:  # no extension specified, use extension regex to filter
            extensionless_re = re.compile(r'^{0}(\..+)?$'.format(re.escape(filename)))
            # why doesn't Python have first()?
            try:
                # FIXME: store extensionless in a separate direct lookup?
                filepath = next(os.path.join(r, f) for r, f in self._dirtree if extensionless_re.match(f))
            except StopIteration:
                raise IOError("couldn't find {0}".format(filename))
        else:  # actual filename, just look it up
            # FIXME: this case sucks; make it a lookup
            try:
                filepath = next(os.path.join(r, f) for r, f in self._dirtree if f == filename)
            except StopIteration:
                raise IOError("couldn't find {0}".format(filename))

        return filepath

    def get_data(self, filename):
        found_file = self.find_file(filename)

        with open(found_file, 'rb') as fd:
            return fd.read()


# TODO: implement these for easier inline debugging?
#    def get_source(self, fullname):
#    def get_code(self, fullname):
#    def is_package(self, fullname):


class AnsibleCollectionRef:
    # FUTURE: introspect plugin loaders to get these dynamically?
    VALID_REF_TYPES = frozenset(['action', 'become', 'cache', 'callback', 'cliconf', 'connection', 'doc_fragments',
                                 'filter', 'httpapi', 'inventory', 'lookup', 'module_utils', 'modules', 'netconf',
                                 'role', 'shell', 'strategy', 'terminal', 'test', 'vars'])

    # FIXME: tighten this up to match Python identifier reqs, etc
    VALID_COLLECTION_NAME_RE = re.compile(to_text(r'^(\w+)\.(\w+)$'))
    VALID_SUBDIRS_RE = re.compile(to_text(r'^\w+(\.\w+)*$'))
    VALID_FQCR_RE = re.compile(to_text(r'^\w+\.\w+\.\w+(\.\w+)*$'))  # can have N included subdirs as well

    def __init__(self, collection_name, subdirs, resource, ref_type):
        """
        Create an AnsibleCollectionRef from components
        :param collection_name: a collection name of the form 'namespace.collectionname'
        :param subdirs: optional subdir segments to be appended below the plugin type (eg, 'subdir1.subdir2')
        :param resource: the name of the resource being references (eg, 'mymodule', 'someaction', 'a_role')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        """
        # FIXME: text type strings

        if not self.is_valid_collection_name(collection_name):
            raise ValueError('invalid collection name (must be of the form namespace.collection): {0}'.format(collection_name))

        if ref_type not in self.VALID_REF_TYPES:
            raise ValueError('invalid collection ref_type: {0}'.format(ref_type))

        self.collection = collection_name
        if subdirs:
            if not re.match(self.VALID_SUBDIRS_RE, subdirs):
                raise ValueError('invalid subdirs entry: {0} (must be empty/None or of the form subdir1.subdir2)'.format(subdirs))
            self.subdirs = subdirs
        else:
            self.subdirs = ''

        self.resource = resource
        self.ref_type = ref_type

        package_components = ['ansible_collections', self.collection]

        if self.ref_type == 'role':
            package_components.append('roles')
        else:
            # we assume it's a plugin
            package_components += ['plugins', self.ref_type]

        if self.subdirs:
            package_components.append(self.subdirs)

        if self.ref_type == 'role':
            # roles are their own resource
            package_components.append(self.resource)

        self.python_package_name = '.'.join(package_components)

    @staticmethod
    def from_fqcr(ref, ref_type):
        """
        Parse a string as a fully-qualified collection reference, raises ValueError if invalid
        :param ref: collection reference to parse (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        :return: a populated AnsibleCollectionRef object
        """
        # assuming the fq_name is of the form (ns).(coll).(optional_subdir_N).(resource_name),
        # we split the resource name off the right, split ns and coll off the left, and we're left with any optional
        # subdirs that need to be added back below the plugin-specific subdir we'll add. So:
        # ns.coll.resource -> ansible_collections.ns.coll.plugins.(plugintype).resource
        # ns.coll.subdir1.resource -> ansible_collections.ns.coll.plugins.subdir1.(plugintype).resource
        # ns.coll.rolename -> ansible_collections.ns.coll.roles.rolename
        if not AnsibleCollectionRef.is_valid_fqcr(ref):
            raise ValueError('{0} is not a valid collection reference'.format(to_native(ref)))

        ref = to_text(ref)

        resource_splitname = ref.rsplit('.', 1)
        package_remnant = resource_splitname[0]
        resource = resource_splitname[1]

        # split the left two components of the collection package name off, anything remaining is plugin-type
        # specific subdirs to be added back on below the plugin type
        package_splitname = package_remnant.split('.', 2)
        if len(package_splitname) == 3:
            subdirs = package_splitname[2]
        else:
            subdirs = ''

        collection_name = '.'.join(package_splitname[0:2])

        return AnsibleCollectionRef(collection_name, subdirs, resource, ref_type)

    @staticmethod
    def try_parse_fqcr(ref, ref_type):
        """
        Attempt to parse a string as a fully-qualified collection reference, returning None on failure (instead of raising an error)
        :param ref: collection reference to parse (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: the type of the reference, eg 'module', 'role', 'doc_fragment'
        :return: a populated AnsibleCollectionRef object on successful parsing, else None
        """
        try:
            return AnsibleCollectionRef.from_fqcr(ref, ref_type)
        except ValueError:
            pass

    @staticmethod
    def legacy_plugin_dir_to_plugin_type(legacy_plugin_dir_name):
        """
        Utility method to convert from a PluginLoader dir name to a plugin ref_type
        :param legacy_plugin_dir_name: PluginLoader dir name (eg, 'action_plugins', 'library')
        :return: the corresponding plugin ref_type (eg, 'action', 'role')
        """
        plugin_type = legacy_plugin_dir_name.replace('_plugins', '')

        if plugin_type == 'library':
            plugin_type = 'modules'

        return plugin_type

    @staticmethod
    def is_valid_fqcr(ref, ref_type=None):
        """
        Validates if is string is a well-formed fully-qualified collection reference (does not look up the collection itself)
        :param ref: candidate collection reference to validate (a valid ref is of the form 'ns.coll.resource' or 'ns.coll.subdir1.subdir2.resource')
        :param ref_type: optional reference type to enable deeper validation, eg 'module', 'role', 'doc_fragment'
        :return: True if the collection ref passed is well-formed, False otherwise
        """

        ref = to_text(ref)

        if not ref_type:
            return bool(re.match(AnsibleCollectionRef.VALID_FQCR_RE, ref))

        return bool(AnsibleCollectionRef.try_parse_fqcr(ref, ref_type))

    @staticmethod
    def is_valid_collection_name(collection_name):
        """
        Validates if is string is a well-formed collection name (does not look up the collection itself)
        :param collection_name: candidate collection name to validate (a valid name is of the form 'ns.collname')
        :return: True if the collection name passed is well-formed, False otherwise
        """

        collection_name = to_text(collection_name)

        return bool(re.match(AnsibleCollectionRef.VALID_COLLECTION_NAME_RE, collection_name))


def get_collection_role_path(role_name, collection_list=None):
    acr = AnsibleCollectionRef.try_parse_fqcr(role_name, 'role')

    if acr:
        # looks like a valid qualified collection ref; skip the collection_list
        role = acr.resource
        collection_list = [acr.collection]
    elif not collection_list:
        return None  # not a FQ role and no collection search list spec'd, nothing to do
    else:
        role = role_name  # treat as unqualified, loop through the collection search list to try and resolve

    for collection_name in collection_list:
        try:
            acr = AnsibleCollectionRef(collection_name=collection_name, subdirs=acr.subdirs, resource=acr.resource, ref_type=acr.ref_type)
            # FIXME: error handling/logging; need to catch any import failures and move along

            # FIXME: this line shouldn't be necessary, but py2 pkgutil.get_data is delegating back to built-in loader when it shouldn't
            pkg = import_module(acr.python_package_name)

            if pkg is not None:
                # the package is now loaded, get the collection's package and ask where it lives
                path = os.path.dirname(to_bytes(sys.modules[acr.python_package_name].__file__, errors='surrogate_or_strict'))
                return role, to_text(path, errors='surrogate_or_strict'), collection_name

        except IOError:
            continue
        except Exception as ex:
            # FIXME: pick out typical import errors first, then error logging
            continue

    return None


def set_collection_playbook_paths(b_playbook_paths):
    AnsibleCollectionLoader().set_playbook_paths(b_playbook_paths)
