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

An example YAML config:

cache_root: /mnt/stagecache
cache_size: 1.5e+12
deault_time: 1-0:00
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

The default config is below under DEFAULT_CONFIG. See types.py for asset types.

"""

import logging
import os
import yaml
import json
from jme.stagecache import types

config = {}

DEFAULT_CONFIG = {
    'cache_root': '~/.cache',
    'asset_types': types.asset_types
}

CONFIG_LOCATIONS = [
    '/etc/stagecache.d/config',
    '{cache_root}/.stagecache.global/config',
    '{user_home}/.config/stagecache/config'
]

CONFIG_ERR = """Config file %s is not valid YAML nor JSON!
 JSON: %r
 YAML: %r
""" 

def get_config():
    if len(config) == 0:
        apply_defaults(config, load_config())
    logging.debug("CONFIG is: " + repr(config))
    return config


def apply_defaults(config, defaults):
    """ recursively apply defaults to nested dicts """
    for param, pdefaults in defaults.items():
        if isinstance(pdefaults, dict):
            apply_defaults(config.setdefault(param, {}), pdefaults)
        else:
            config.setdefault(param, pdefaults)

def load_config(cache_root=None):
    """ loop over predefined locations to read in config values """
    user_home = os.path.expanduser("~")
    config = dict(DEFAULT_CONFIG)
    for config_template in CONFIG_LOCATIONS:
        cache_root = config['cache_root']
        config_file = config_template.format(**locals())
        if os.path.exists(config_file):
            config = apply_defaults(load_config_file(config_file), config)

    types.cleanup_asset_types(config['asset_types'])
    return config

def load_config_file(config_file):
    """ attempt to load as YAML, then as JSON """
    try:
        return load_yaml_config(config_file)
    except yaml.error.YAMLError as yerr:
        pass

    try:
        return load_json_config(config_file)
    except json.decoder.JSONDecodeError as jerr:
        logging.error(PARSE_ERR, config_file, yerr, jerr)
        raise Exception("Could not load config file: " + config_file)


def load_yaml_config(config_file):
    with open(config_file) as config_handle:
        return yaml.load(config_handle, Loader=yaml.FullLoader)

def load_json_config(config_file):
    with open(config_file) as config_handle:
        return json.load(config_handle)
    
