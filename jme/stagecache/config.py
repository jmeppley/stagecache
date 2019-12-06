"""
Attempts to read  configuration files from ALL of the following locations
in the order listed. Values in any file will override values from all
previously read files.

    * global config: /etc/stagecache.d/config
    * cache config: {cache_root}/.stagecache.global/config
    * user config: $HOME/.config/stagecache/config
    * (command line arguments)

Formats listed below will be attempted in order unilt parsing throws no errors:

    * YAML
    * JSON

An example YAML config below. The cache location and defults can be set
globally or in the 'caches' dict. The global 'cache_*' variables are used
as defaults for any cache without explicit settings. If no global cache_root
given, a cache named 'default' is used. If that doesn't exists, the first cache listed is the default.

cache_root: /mnt/stagecache
cache_size: 1.5e+12
cache_time: 1-0:00
caches:
    home:
        root: ~/.cache
        size: 1.0e+10
        time: 12:00
        umask: "664"
remote:
    mappings:
        - pattern: "/mnt/(nas_[^/]+)/(.+)"
          host_repl: "\\1.hawaii.edu"
          path_repl: "/mnt/tank/\\2"
    SFTP:
        default:
            username: jmeppley
            private_key: ~/.ssh/id_rsa
        public.server.edu:
            username: anonymous
asset_types:
    taxdump:
        suff_list:
            - "/nodes.dmp"
            - /names.dmp
    bwadb:
        suff_patt: '\\.[a-z]+$'

NOTES:
    * cache size is in bytes
    * if cache_size is not specified, will check filesystem free space
    * private key is optional, will try all if not given
    * username defaults to local username
    * asset types above are some of the defaults, given here as examples
    * cache time is specfied in the SLURM format [days-]hours:min[:secs]
    * if named cahces are configured, users can specify with either path or
    name
    * the caches list is ignored if it's in a cache config
    * umask must be quoted or an octal ("664" or 0o664)

The default config is below under DEFAULT_CONFIG. See types.py for asset types.

"""

import logging
import os
import yaml
import json
from copy import deepcopy
from jme.stagecache import types

LOGGER = logging.getLogger(name='config')

# read and cache config file contents separately
CONFIGS = {}

DEFAULT_CONFIG = {
    'cache_root': '~/.cache',
    'cache_time': '1-0:00',
    'cache_umask': '664',
    'asset_types': types.asset_types
}

# config file locations
GLOBAL_CONFIG = '/etc/stagecache.d/config'
CACHE_CONFIG_TEMPLATE = '{cache_root}/.stagecache.global/config'
USER_CONFIG = '{user_home}/.config/stagecache/config'.format(
    user_home=os.path.expanduser("~")
)

CONFIG_ERR = """Config file %s is not valid YAML nor JSON!
 JSON: %r
 YAML: %r
""" 

def get_config(cache=None):
    """ get cache specific configuration from name or path """

    # make sure global settings are loaded
    load_configs()

    if cache is None:
        cache = CONFIGS['default_cache']
        if cache is None:
            cache = os.path.abspath(os.path.expanduser("~/.cache"))
    
    # look in already loaded cache configs to see if its a named cache
    LOGGER.debug("Looking for config for " + str(cache))
    cache_root = os.path.abspath(os.path.expanduser(cache))
    if cache in CONFIGS['cache_names']:
        cache_name = cache
        cache_root = CONFIGS['cache_names'][cache]
    elif cache_root in CONFIGS['cache_roots']:
        cache_name = CONFIGS['cache_roots'][cache_root]
    else:
        cache_name = None

    # load cache config file
    cache_config = load_cache_config(cache_root)

    # move any globale cache settings into caches
    cache_config['caches'] = {cache_name: {'root': cache_root}}
    for k in ['size', 'time', 'umask']:
        root_k = 'cache_' + k
        if root_k in cache_config:
            cache_config['caches'][cache_name][k] = cache_config[root_k]
            del cache_config[root_k]

    # merge configs in order
    config = None
    for default in [CONFIGS['user'],
                    cache_config,
                    CONFIGS['global'],
                    DEFAULT_CONFIG]:
        if config is None:
            config = deepcopy(default)
        else:
            apply_defaults(config, default)

    # copy cache specific settings to top level
    for k in ['root', 'size', 'time', 'umask']:
        root_k = 'cache_' + k
        if k in config['caches'][cache_name]:
            config[root_k] = config['caches'][cache_name][k]

    # get the umask in the right foramt
    config['cache_umask'] = fix_umask(config['cache_umask'])

    LOGGER.info("Loaded config for " + cache_root)
    LOGGER.debug(repr(config))
    return config

def fix_umask(umask):
    # make sure it's an int
    if isinstance(umask, str):
        if int(umask) == eval(umask):
            # it must be an octal, not a straight int
            umask = "0o" + umask
        umask = eval(umask)
    return umask

def load_cache_config(cache_root):
    config_file = CACHE_CONFIG_TEMPLATE.format(cache_root=cache_root)
    return load_config_file(config_file)

def apply_defaults(config, defaults):
    """ recursively apply defaults to nested dicts """
    for param, pdefaults in defaults.items():
        if isinstance(pdefaults, dict):
            apply_defaults(config.setdefault(param, {}), pdefaults)
        else:
            # only sets value if not already present
            config.setdefault(param, deepcopy(pdefaults))


def load_configs():
    """ load globa and user configs """
    if 'global' not in CONFIGS:
        # global settings
        LOGGER.debug('Getting settings from global file: %s', GLOBAL_CONFIG)
        CONFIGS['global'] = load_config_file(GLOBAL_CONFIG)
        # user settings
        CONFIGS['user'] = load_config_file(USER_CONFIG)
        # place holder for cache-specific configs
        CONFIGS['caches'] = {}

        # pre-load lookup table from cache path to name
        CONFIGS['cache_roots'] = {}
        CONFIGS['cache_names'] = {}
        first_global_cache = None
        for name, root in CONFIGS['global'].get('caches', {}).items():
            root = os.path.abspath(os.path.expanduser(root))
            if first_global_cache is None:
                first_global_cache = name
            CONFIGS['cache_roots'][root] = name
            CONFIGS['cache_names'][name] = root
        first_user_cache = None
        for name, root in CONFIGS['user'].get('caches', {}).items():
            root = os.path.abspath(os.path.expanduser(root))
            if first_user_cache is None:
                first_user_cache = name
            CONFIGS['cache_roots'][root] = name
            CONFIGS['cache_names'][name] = root

        # set default cache
        if 'cache_root' in CONFIGS['user']:
            default = CONFIGS['user']['cache_root']
        elif 'cache_root' in CONFIGS['global']:
            default = CONFIGS['global']['cache_root']
        elif 'default' in CONFIGS['user'].get('caches', {}) \
                or 'default' in CONFIGS['global'].get('caches', {}):
            default = 'default'
        elif len(CONFIGS['user'].get('caches', {})) > 0:
            default = next(iter(CONFIGS['user']['caches'].keys()))
        elif len(CONFIGS['global'].get('caches', {})) > 0:
            default = next(iter(CONFIGS['global']['caches'].keys()))
        else:
            default = None
        CONFIGS['default_cache'] = default


def load_config_file(config_file):
    """ attempt to load as YAML, then as JSON """

    LOGGER.info("Loading config from " + config_file)
    if not os.path.exists(config_file):
        LOGGER.debug("skipping missing config file")
        return {}

    try:
        return load_yaml_config(config_file)
    except yaml.error.YAMLError as yerr:
        pass

    try:
        return load_json_config(config_file)
    except json.decoder.JSONDecodeError as jerr:
        LOGGER.error(PARSE_ERR, config_file, yerr, jerr)
        raise Exception("Could not load config file: " + config_file)


def load_yaml_config(config_file):
    with open(config_file) as config_handle:
        return yaml.load(config_handle, Loader=yaml.FullLoader)

def load_json_config(config_file):
    with open(config_file) as config_handle:
        return json.load(config_handle)
