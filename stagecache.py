#!/usr/bin/env python
"""
stagecache.py

Given a path to a resource (usually a file),

 * look for file in local chache
 * copy file to cache if missing
 * return path to cached file

Caches to /tmp by default, but new location can be configured:
    * with command line options (see below)
    * in local config file: .stagecache.yaml
    * in user config file: ~/.config/stagecache.yaml
    * in global config file: ${SCRIPT_PATH}/../etc/stagecache.yaml

Limited support for groups of files:
    * formated lastdb files
    * TDB...

default cache root and cache lifetimes are configurable (see config.py).
Fallback values are: ~/.cache and one day (1-0:00).

Use bash magic to embed in a command. EG:
    lastal $(stagecache.py -t last /path/to/db) /path/to/query.fasta

Run with no TARGET_PATH to get the number of files and free space in cache. Add
--verbose or --debug (or -v or -d) to get list of files in cache.

Usage:
    stagecache.py [options] TARGET_PATH
    stagecache.py [options] [ --yaml | --json ]
    stagecache.py -h | --help
    stagecache.py -V | --version

Options:
    -h --help                Show this screen.
    -V --version             Show version.
    -v --verbose             Print more messages.
    -d --debug               Print even more messages.
    --force                  Delete any write_locks
    -a ATYPE, --atype ATYPE  Asset type [default: file]
    -c CACHE, --cache CACHE  Cache root
    -t TIME, --time TIME     Keep in cache for at least this time
"""

import logging
import os
import sys
import json
import yaml
from docopt import docopt
from jme.stagecache.main import cache_target, query_cache
from jme.stagecache import VERSION
from jme.stagecache.util import human_readable_bytes

def main(arguments):
    """ The starting point for command line operation
    
    Takes arguments from docopt (see 'if' block at end)

    Arguments from docopt like:
    {
          "--help": false, 
          "--verbose": true, 
          "--time": false, 
          "--version": false, 
          "--cache": None,
          "--atype": None,
          "TARGET_PATH": "/path/to/target.ext",
    }
    """

    # help and version options handled by docopt

    # collect arguments that affect function
    target_path = arguments['TARGET_PATH']
    kwargs = {k:arguments["--"+k] \
              for k in ['time', 'cache', 'atype', 'force']}

    # logging
    if arguments['--debug']:
        log_level = logging.DEBUG
        ll_text = 'debug'
    elif arguments['--verbose']:
        log_level = logging.INFO
        ll_text = 'verbose'
    else:
        log_level = logging.WARNING
        ll_text = 'quiet'
    logging.basicConfig(level=log_level)
    logging.info("Log level set to %s (%s)" % (log_level, ll_text))

    logging.debug(arguments)

    if target_path is not None:
        print(cache_target(target_path, **kwargs))
    else:
        cache_data = query_cache(**kwargs)
        if arguments['--json']:
            print(json.dumps(cache_data, indent=1))
        elif arguments['--yaml']:
            print(yaml.dump(cache_data, indent=1))
        else:
            print("{} used and {} available in {}".format(
                human_readable_bytes(cache_data['used']),
                human_readable_bytes(cache_data['free']),
                cache_data['root']))

            # print file details if verbose or debugging
            if log_level <= logging.INFO:
                for file_data in cache_data['files']:
                    print("{} ({}) uses {} for {:0.0f}s".format(
                        file_data['target'],
                        file_data['type'],
                        human_readable_bytes(file_data['size']),
                        file_data['lock'],
                    ))

if __name__ == '__main__':
    import sys
    arguments = docopt(__doc__, version=VERSION)
    main(arguments)

