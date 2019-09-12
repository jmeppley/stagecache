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
    * formateed lastdb files
    * TDB...

Use bash magic to embed in a command. EG:
    lastal $(stagecache.py -t last /path/to/db) /path/to/query.fasta

Usage:
    stagecache.py [options] TARGET_PATH
    stagecache.py
    stagecache -h | --help
    stagecache -V | --version

Options:
    -h --help                Show this screen.
    -V --version             Show version.
    -v --verbose             Print more messages.
    -d --debug               Print even more messages.
    -a ATYPE, --atype ATYPE  Asset type (default to single file)
    -c CACHE, --cache CACHE  Cache root
    -t TIME, --time TIME     Keep in cache for (default: 1-0:00 (1 day))
"""

import logging
import os
import sys
from docopt import docopt
from jme.stagecache import cache_target

VERSION = "0.0.1"

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
              for k in ['time', 'cache', 'atype'] \
              if "--"+k in arguments}

    # logging
    if '--debug' in arguments:
        log_level = logging.DEBUG
        ll_text = 'debug'
    elif '--verbose' in arguments:
        log_level = logging.INFO
        ll_text = 'verbose'
    logging.basicConfig(level=loglevel)
    logging.info("Log level set to %r(%d)" % (loglevel, ll_text))

    print(cache_target(target_path, **kwargs))


if __name__ == '__main__':
    import sys
    print(sys.argv)
    arguments = docopt(__doc__, version=VERSION)
    main(arguments)

