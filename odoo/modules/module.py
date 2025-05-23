# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import ast
import collections.abc
import copy
import functools
import importlib
import logging
import os
import pkg_resources
import re
import sys
import warnings
from os.path import join as opj, normpath

import odoo
import odoo.tools as tools
import odoo.release as release
from odoo.tools import pycompat

MANIFEST_NAMES = ('__manifest__.py', '__openerp__.py')
README = ['README.rst', 'README.md', 'README.txt']

_DEFAULT_MANIFEST = {
    #addons_path: f'/path/to/the/addons/path/of/{module}',  # automatic
    'application': False,
    'bootstrap': False,  # web
    'assets': {},
    'author': 'Odoo S.A.',
    'auto_install': False,
    'category': 'Uncategorized',
    'data': [],
    'demo': [],
    'demo_xml': [],
    'depends': [],
    'description': '',
    'external_dependencies': {},
    #icon: f'/{module}/static/description/icon.png',  # automatic
    'init_xml': [],
    'installable': True,
    'images': [],  # website
    'images_preview_theme': {},  # website themes
    #license, mandatory
    'live_test_url': '',  # website themes
    #name, mandatory
    'post_init_hook': '',
    'post_load': None,
    'pre_init_hook': '',
    'sequence': 100,
    'snippet_lists': {},  # website themes
    'summary': '',
    'test': [],
    'update_xml': [],
    'uninstall_hook': '',
    'version': '1.0',
    'web': False,
    'website': '',
}

_logger = logging.getLogger(__name__)

# addons path as a list
# ad_paths is a deprecated alias, please use odoo.addons.__path__
@tools.lazy
def ad_paths():
    warnings.warn(
        '"odoo.modules.module.ad_paths" is a deprecated proxy to '
        '"odoo.addons.__path__".', DeprecationWarning, stacklevel=2)
    return odoo.addons.__path__

# Modules already loaded
loaded = []

class AddonsHook(object):
    """ Makes modules accessible through openerp.addons.* """

    def find_module(self, name, path=None):
        if name.startswith('openerp.addons.') and name.count('.') == 2:
            warnings.warn(
                '"openerp.addons" is a deprecated alias to "odoo.addons".',
                DeprecationWarning, stacklevel=2)
            return self

    def load_module(self, name):
        assert name not in sys.modules

        odoo_name = re.sub(r'^openerp.addons.(\w+)$', r'odoo.addons.\g<1>', name)

        odoo_module = sys.modules.get(odoo_name)
        if not odoo_module:
            odoo_module = importlib.import_module(odoo_name)

        sys.modules[name] = odoo_module

        return odoo_module

class OdooHook(object):
    """ Makes odoo package also available as openerp """

    def find_module(self, name, path=None):
        # openerp.addons.<identifier> should already be matched by AddonsHook,
        # only framework and subdirectories of modules should match
        if re.match(r'^openerp\b', name):
            warnings.warn(
                'openerp is a deprecated alias to odoo.',
                DeprecationWarning, stacklevel=2)
            return self

    def load_module(self, name):
        assert name not in sys.modules

        canonical = re.sub(r'^openerp(.*)', r'odoo\g<1>', name)

        if canonical in sys.modules:
            mod = sys.modules[canonical]
        else:
            # probable failure: canonical execution calling old naming -> corecursion
            mod = importlib.import_module(canonical)

        # just set the original module at the new location. Don't proxy,
        # it breaks *-import (unless you can find how `from a import *` lists
        # what's supposed to be imported by `*`, and manage to override it)
        sys.modules[name] = mod

        return sys.modules[name]


class UpgradeHook(object):
    """Makes the legacy `migrations` package being `odoo.upgrade`"""

    def find_module(self, name, path=None):
        if re.match(r"^odoo.addons.base.maintenance.migrations\b", name):
            # We can't trigger a DeprecationWarning in this case.
            # In order to be cross-versions, the multi-versions upgrade scripts (0.0.0 scripts),
            # the tests, and the common files (utility functions) still needs to import from the
            # legacy name.
            return self

    def load_module(self, name):
        assert name not in sys.modules

        canonical_upgrade = name.replace("odoo.addons.base.maintenance.migrations", "odoo.upgrade")

        if canonical_upgrade in sys.modules:
            mod = sys.modules[canonical_upgrade]
        else:
            mod = importlib.import_module(canonical_upgrade)

        sys.modules[name] = mod

        return sys.modules[name]


def initialize_sys_path():
    """
    Setup the addons path ``odoo.addons.__path__`` with various defaults
    and explicit directories.
    """
    # hook odoo.addons on data dir
    dd = os.path.normcase(tools.config.addons_data_dir)
    if os.access(dd, os.R_OK) and dd not in odoo.addons.__path__:
        odoo.addons.__path__.append(dd)

    # hook odoo.addons on addons paths
    for ad in tools.config['addons_path'].split(','):
        ad = os.path.normcase(os.path.abspath(tools.ustr(ad.strip())))
        if ad not in odoo.addons.__path__:
            odoo.addons.__path__.append(ad)

    # hook odoo.addons on base module path
    base_path = os.path.normcase(os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'addons')))
    if base_path not in odoo.addons.__path__ and os.path.isdir(base_path):
        odoo.addons.__path__.append(base_path)

    # hook odoo.upgrade on upgrade-path
    from odoo import upgrade
    legacy_upgrade_path = os.path.join(base_path, 'base', 'maintenance', 'migrations')
    for up in (tools.config['upgrade_path'] or legacy_upgrade_path).split(','):
        up = os.path.normcase(os.path.abspath(tools.ustr(up.strip())))
        if up not in upgrade.__path__:
            upgrade.__path__.append(up)

    # create decrecated module alias from odoo.addons.base.maintenance.migrations to odoo.upgrade
    spec = importlib.machinery.ModuleSpec("odoo.addons.base.maintenance", None, is_package=True)
    maintenance_pkg = importlib.util.module_from_spec(spec)
    maintenance_pkg.migrations = upgrade
    sys.modules["odoo.addons.base.maintenance"] = maintenance_pkg
    sys.modules["odoo.addons.base.maintenance.migrations"] = upgrade

    # hook deprecated module alias from openerp to odoo and "crm"-like to odoo.addons
    if not getattr(initialize_sys_path, 'called', False): # only initialize once
        sys.meta_path.insert(0, UpgradeHook())
        sys.meta_path.insert(0, OdooHook())
        sys.meta_path.insert(0, AddonsHook())
        initialize_sys_path.called = True


def normalize_manifest(manifest):
    """
    Normalizza i dati del manifest per assicurarsi che siano nel formato corretto.
    Corregge e sanitizza tutti i campi del manifest per prevenire errori.
    """
    # Correzione dei tipi di base
    if not isinstance(manifest.get('application'), bool):
        manifest['application'] = bool(manifest.get('application'))
    
    if not isinstance(manifest.get('bootstrap'), bool):
        manifest['bootstrap'] = bool(manifest.get('bootstrap'))
    
    if not isinstance(manifest.get('installable'), bool):
        manifest['installable'] = bool(manifest.get('installable'))
    
    if not isinstance(manifest.get('web'), bool):
        manifest['web'] = bool(manifest.get('web'))
    
    # Normalizza assets (deve essere un dict)
    if not isinstance(manifest.get('assets', {}), dict):
        manifest['assets'] = {}
    
    # Normalizza external_dependencies (deve essere un dict)
    if not isinstance(manifest.get('external_dependencies', {}), dict):
        manifest['external_dependencies'] = {}
    
    # Normalizza dipendenze (devono essere liste)
    list_fields = [
        'depends', 'data', 'demo', 'demo_xml', 'init_xml', 
        'update_xml', 'test', 'images'
    ]
    
    for field in list_fields:
        if not isinstance(manifest.get(field, []), list):
            manifest[field] = []
    
    # Normalizza campi dizionario
    dict_fields = [
        'images_preview_theme', 'snippet_lists'
    ]
    
    for field in dict_fields:
        if not isinstance(manifest.get(field, {}), dict):
            manifest[field] = {}
    
    # Normalizza auto_install in modo speciale
    if isinstance(manifest.get('auto_install'), dict):
        manifest['auto_install'] = False
    elif isinstance(manifest.get('auto_install'), (list, tuple, set)):
        # Se è una lista/tupla/set, verifichiamo che tutti gli elementi siano stringhe
        try:
            auto_install_list = list(manifest['auto_install'])
            # Converti solo se tutti gli elementi sono stringhe
            if all(isinstance(item, str) for item in auto_install_list):
                manifest['auto_install'] = auto_install_list
            else:
                manifest['auto_install'] = False
        except (TypeError, ValueError):
            manifest['auto_install'] = False
    
    return manifest


def check_manifest_dependencies(module_name, manifest=None):
    """
    Check if all dependencies of a module specified in its manifest are met.
    
    :param module_name: The name of the module
    :param manifest: The manifest dictionary of the module (optional)
    :return: True if all dependencies are met, False otherwise
    """
    try:
        if manifest is None:
            manifest = get_manifest(module_name)
        
        if not manifest:
            return False
        
        # Check regular module dependencies
        dependencies = manifest.get('depends', [])
        if not isinstance(dependencies, list):
            # Se dependencies non è una lista, convertiamolo in una lista vuota per sicurezza
            dependencies = []
        
        if not dependencies:
            return True
        
        # Check if all dependencies are installed and loaded
        available_modules = set(get_modules())
        
        # Assicuriamoci che ogni dipendenza sia una stringa prima di verificarla
        for dep in dependencies:
            if not isinstance(dep, str) or dep not in available_modules:
                return False
        
        return True
    except Exception as e:
        _logger.error("Error in check_manifest_dependencies: %s", e)
        return False

def check_external_dependencies(manifest):
    """
    Check if all external dependencies of a module specified in its manifest are met.
    
    :param manifest: The manifest dictionary of the module
    :return: True if all external dependencies are met, False otherwise
    """
    try:
        external_deps = manifest.get('external_dependencies', {})
        
        # Se external_dependencies non è un dizionario, consideriamolo come vuoto
        if not isinstance(external_deps, dict):
            return True
        
        # Verifica delle dipendenze Python
        python_deps = external_deps.get('python', [])
        if isinstance(python_deps, list):
            for dep in python_deps:
                if isinstance(dep, str):
                    try:
                        importlib.import_module(dep)
                    except ImportError:
                        return False
        
        # Verifica delle dipendenze binarie
        bin_deps = external_deps.get('bin', [])
        if isinstance(bin_deps, list):
            for dep in bin_deps:
                if isinstance(dep, str):
                    if not tools.find_in_path(dep):
                        return False
        
        return True
    except Exception as e:
        _logger.error("Error in check_external_dependencies: %s", e)
        return False

def get_module_path(module, downloaded=False, display_warning=True):
    """Return the path of the given module.

    Search the addons paths and return the first path where the given
    module is found. If downloaded is True, return the default addons
    path if nothing else is found.

    """
    for adp in odoo.addons.__path__:
        files = [opj(adp, module, manifest) for manifest in MANIFEST_NAMES] +\
                [opj(adp, module + '.zip')]
        if any(os.path.exists(f) for f in files):
            return opj(adp, module)

    if downloaded:
        return opj(tools.config.addons_data_dir, module)
    if display_warning:
        _logger.warning('module %s: module not found', module)
    return False

def get_module_filetree(module, dir='.'):
    warnings.warn(
        "Since 16.0: use os.walk or a recursive glob or something",
        DeprecationWarning,
        stacklevel=2
    )
    path = get_module_path(module)
    if not path:
        return False

    dir = os.path.normpath(dir)
    if dir == '.':
        dir = ''
    if dir.startswith('..') or (dir and dir[0] == '/'):
        raise Exception('Cannot access file outside the module')

    files = odoo.tools.osutil.listdir(path, True)

    tree = {}
    for f in files:
        if not f.startswith(dir):
            continue

        if dir:
            f = f[len(dir)+int(not dir.endswith('/')):]
        lst = f.split(os.sep)
        current = tree
        while len(lst) != 1:
            current = current.setdefault(lst.pop(0), {})
        current[lst.pop(0)] = None

    return tree

def get_resource_path(module, *args):
    """Return the full path of a resource of the given module.

    :param module: module name
    :param list(str) args: resource path components within module

    :rtype: str
    :return: absolute path to the resource

    TODO make it available inside on osv object (self.get_resource_path)
    """
    mod_path = get_module_path(module)
    if not mod_path:
        return False
    return check_resource_path(mod_path, *args)

def check_resource_path(mod_path, *args):
    resource_path = opj(mod_path, *args)
    if os.path.exists(resource_path):
        return resource_path
    return False

# backwards compatibility
get_module_resource = get_resource_path

def get_resource_from_path(path):
    """Tries to extract the module name and the resource's relative path
    out of an absolute resource path.

    If operation is successful, returns a tuple containing the module name, the relative path
    to the resource using '/' as filesystem seperator[1] and the same relative path using
    os.path.sep seperators.

    [1] same convention as the resource path declaration in manifests

    :param path: absolute resource path

    :rtype: tuple
    :return: tuple(module_name, relative_path, os_relative_path) if possible, else None
    """
    resource = False
    for adpath in odoo.addons.__path__:
        # force trailing separator
        adpath = os.path.join(adpath, "")
        if os.path.commonprefix([adpath, path]) == adpath:
            resource = path.replace(adpath, "", 1)
            break

    if resource:
        relative = resource.split(os.path.sep)
        if not relative[0]:
            relative.pop(0)
        module = relative.pop(0)
        return (module, '/'.join(relative), os.path.sep.join(relative))
    return None

def get_module_icon(module):
    iconpath = ['static', 'description', 'icon.png']
    if get_module_resource(module, *iconpath):
        return ('/' + module + '/') + '/'.join(iconpath)
    return '/base/'  + '/'.join(iconpath)

def module_manifest(path):
    """Returns path to module manifest if one can be found under `path`, else `None`."""
    if not path:
        return None
    for manifest_name in MANIFEST_NAMES:
        if os.path.isfile(opj(path, manifest_name)):
            return opj(path, manifest_name)

def get_module_root(path):
    """
    Get closest module's root beginning from path

        # Given:
        # /foo/bar/module_dir/static/src/...

        get_module_root('/foo/bar/module_dir/static/')
        # returns '/foo/bar/module_dir'

        get_module_root('/foo/bar/module_dir/')
        # returns '/foo/bar/module_dir'

        get_module_root('/foo/bar')
        # returns None

    @param path: Path from which the lookup should start

    @return:  Module root path or None if not found
    """
    while not module_manifest(path):
        new_path = os.path.abspath(opj(path, os.pardir))
        if path == new_path:
            return None
        path = new_path
    return path

def load_manifest(module, mod_path=None):
    """ Load the module manifest from the file system. """
    try:
        if not mod_path:
            mod_path = get_module_path(module, downloaded=True)
        manifest_file = module_manifest(mod_path)

        if not manifest_file:
            _logger.debug('module %s: no manifest file found %s', module, MANIFEST_NAMES)
            return {}

        manifest = copy.deepcopy(_DEFAULT_MANIFEST)
        manifest['icon'] = get_module_icon(module)

        with tools.file_open(manifest_file, mode='r') as f:
            manifest_data = ast.literal_eval(f.read())
            # Convalidiamo la struttura del manifest
            if not isinstance(manifest_data, dict):
                _logger.error("Module %s: manifest file is not a valid dictionary", module)
                return manifest
            manifest.update(manifest_data)

        if not manifest['description']:
            readme_path = [opj(mod_path, x) for x in README
                          if os.path.isfile(opj(mod_path, x))]
            if readme_path:
                with tools.file_open(readme_path[0]) as fd:
                    manifest['description'] = fd.read()

        if not manifest.get('license'):
            manifest['license'] = 'LGPL-3'
            _logger.warning("Missing `license` key in manifest for %r, defaulting to LGPL-3", module)

        # Normalizza tutti i campi del manifest
        manifest = normalize_manifest(manifest)

        # Gestione sicura di auto_install
        if isinstance(manifest['auto_install'], (list, tuple)) and not isinstance(manifest['auto_install'], (dict, str)):
            # Converti a lista per essere sicuri
            auto_install_list = list(manifest['auto_install'])
            
            # Verifica che tutti gli elementi siano stringhe
            if all(isinstance(item, str) for item in auto_install_list):
                try:
                    auto_install_set = set(auto_install_list)
                    # Verifica che tutte le dipendenze auto-install siano nella lista delle dipendenze
                    depends_set = set(manifest['depends'])
                    non_dependencies = auto_install_set.difference(depends_set)
                    
                    if non_dependencies:
                        _logger.warning(
                            "auto_install triggers must be dependencies, found "
                            "non-dependencies [%s] for module %s",
                            ', '.join(non_dependencies), module
                        )
                        manifest['auto_install'] = False
                    else:
                        manifest['auto_install'] = auto_install_set
                except (TypeError, ValueError):
                    manifest['auto_install'] = False
            else:
                manifest['auto_install'] = False
        elif manifest['auto_install'] is True:
            try:
                manifest['auto_install'] = set(manifest['depends'])
            except (TypeError, ValueError):
                manifest['auto_install'] = False

        manifest['version'] = adapt_version(manifest['version'])
        manifest['addons_path'] = normpath(opj(mod_path, os.pardir))

        return manifest
    except Exception as e:
        _logger.error("Error loading manifest for module %s: %s", module, e)
        return copy.deepcopy(_DEFAULT_MANIFEST)

@functools.lru_cache(maxsize=None)
def _get_manifest_cached(addon):
    """
    Get the module manifest, from the addon or path.
    This function is a cached version of `get_manifest`.
    """
    return get_manifest(addon)
    
@functools.lru_cache(maxsize=None)
def get_manifest(module, mod_path=None):
    """
    Get the module manifest.

    :param str module: The name of the module (sale, purchase, ...).
    :param Optional[str] mod_path: The optional path to the module on
        the file-system. If not set, it is determined by scanning the
        addons-paths.
    :returns: The module manifest as a dict or an empty dict
        when the manifest was not found.
    :rtype: dict
    """
    return load_manifest(module, mod_path)

def load_information_from_description_file(module, mod_path=None):
    warnings.warn(
        'load_information_from_description_file() is a deprecated '
        'alias to get_manifest()', DeprecationWarning, stacklevel=2)
    return get_manifest(module, mod_path)

def load_openerp_module(module_name):
    """ Load an OpenERP module, if not already loaded.

    This loads the module and register all of its models, thanks to either
    the MetaModel metaclass, or the explicit instantiation of the model.
    This is also used to load server-wide module (i.e. it is also used
    when there is no model to register).
    """
    global loaded
    if module_name in loaded:
        return

    try:
        __import__('odoo.addons.' + module_name)

        # Call the module's post-load hook. This can done before any model or
        # data has been initialized. This is ok as the post-load hook is for
        # server-wide (instead of registry-specific) functionalities.
        info = get_manifest(module_name)
        if info['post_load']:
            getattr(sys.modules['odoo.addons.' + module_name], info['post_load'])()

    except Exception as e:
        msg = "Couldn't load module %s" % (module_name)
        _logger.critical(msg)
        _logger.critical(e)
        raise
    else:
        loaded.append(module_name)

def get_modules():
    """Returns the list of module names
    """
    def listdir(dir):
        def clean(name):
            name = os.path.basename(name)
            if name[-4:] == '.zip':
                name = name[:-4]
            return name

        def is_really_module(name):
            for mname in MANIFEST_NAMES:
                if os.path.isfile(opj(dir, name, mname)):
                    return True
        return [
            clean(it)
            for it in os.listdir(dir)
            if is_really_module(it)
        ]

    plist = []
    for ad in odoo.addons.__path__:
        if not os.path.exists(ad):
            _logger.warning("addons path does not exist: %s", ad)
            continue
        plist.extend(listdir(ad))
    return list(set(plist))

def get_modules_with_version():
    modules = get_modules()
    res = dict.fromkeys(modules, adapt_version('1.0'))
    for module in modules:
        try:
            info = get_manifest(module)
            res[module] = info['version']
        except Exception:
            continue
    return res

def adapt_version(version):
    serie = release.major_version
    if version == serie or not version.startswith(serie + '.'):
        version = '%s.%s' % (serie, version)
    return version

current_test = None