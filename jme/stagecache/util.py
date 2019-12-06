"""
miscelaneous functions

def human_readable_bytes(byt):
def path_up_to_wildcard(full_path):
def parse_url(url, config, use_local=False, has_wildcards=False):
def user_from_config(config, host):
"""


# numpy is faster, but we don't use enough to warrant the extra dependencies
#from numpy import log, power, abs

# use built in python functions
import logging
import getpass
import os
import re
from math import log
from collections import namedtuple
power = pow
LOGGER = logging.getLogger(name='util')

LN_BASE = log(power(1024, 1/3))
def human_readable_bytes(byt):
    """ fixed version of https://stackoverflow.com/a/17754143/663466
     hybrid of https://stackoverflow.com/a/10171475/2595465
      with https://stackoverflow.com/a/5414105/2595465  """
    # return bytes if small
    if byt <= 99:
        return str(int(byt))
    magnitude = int(log(abs(byt)) / LN_BASE)
    if magnitude > 19:
        float_fmt = '%i'
        illion = 20 // 3
    else:
        mag3 = (magnitude+1) % 3
        float_fmt = '%' + str(mag3) + "." + str(3-mag3) + 'f'
        illion = (magnitude + 1) // 3
    format_str = float_fmt + ['', 'K', 'M', 'G', 'T', 'P', 'E'][illion]
    return (format_str % (byt * 1.0 / (1024 ** illion))).lstrip('0')

def path_up_to_wildcard(full_path):
    """ If a given path has a wildcard placeholder ( eg {sample} ),
    return the last directory before that point """
    path_fragment = full_path.split('{')[0]
    if path_fragment == full_path:
        return full_path
    if path_fragment.endswith(os.path.pathsep):
        return path_fragment[:-1]
    return os.path.dirname(path_fragment)

URL_REXP = re.compile(r'^([A-Za-z]+)://(?:([^/@]+)@)?([^/]*)(/.+)$')
Remote = namedtuple('Remote', ['protocol', 'user', 'host', 'path'])


def parse_url(url, config, use_local=False, has_wildcards=False):
    """ check if the string is a url or simple path
    return None if it's a path
    return named tuple with (protocol, user, host, path) if its a URL
    """

    ## Check 1: is it a full formed URL? EG:
    #   SFTP://server.com/path/to/file
    #   file:///local/path
    #   SCP://user@host.dom/some/path
    match = URL_REXP.search(url)
    if match:
        remote = Remote(*match.groups())
        if remote.user is None:
            user = user_from_config(config, remote.host)
            remote = Remote(remote.protocol, user,
                            remote.host, remote.path)
        if remote.protocol.lower == 'file':
            if len(remote.host) > 0:
                raise Exception("file URL should have no host name")
            return None
        return remote

    # skip check 2 if file exists and we're OK using local files
    if use_local:
        if os.path.exists(path_up_to_wildcard(url) \
                          if has_wildcards else url):
            return None


    ## check 2: user configured remote maps
    for custom_patterns in config \
                           .get('remote', {}) \
                           .get('mappings', []):
        try:
            mnt_rexp = re.compile(custom_patterns['pattern'])
            host_repl = custom_patterns['host_repl']
            path_repl = custom_patterns['path_repl']
        except KeyError:
            LOGGER.error("custom patterns must contain: pattern, host_repl, "
                         "and path_repl")
            raise
        except:
            LOGGER.error("re cannot compile custom pattern: " +
                         custom_patterns['pattern'])
            raise

        LOGGER.debug("Checking remote pattern: %r", custom_patterns['pattern'])

        if not mnt_rexp.search(url):
            # skip to next pattern if this doesn't match
            continue

        try:
            source_path = mnt_rexp.sub(path_repl, url)
        except:
            LOGGER.error("re cannot understand replacement expression " +
                         path_repl)
            raise
        try:
            host = mnt_rexp.sub(host_repl, url)
        except:
            LOGGER.error("re cannot understand replacement expression " +
                         host_repl)
            raise
        user = user_from_config(config, host)

        LOGGER.debug("INFERRED URL SFTP://%s@%s%s", user, host, source_path)
        return Remote('SFTP', user, host, source_path)

    ## 3: just a regular, local file
    # we ge here if there was no match above
    return None


def user_from_config(config, host):
    """ get username from config for this host. Fall back to local username """
    local_user = getpass.getuser()
    LOGGER.debug("config: %r", config)
    default_user = config.get('remote', {})\
                         .get('SFTP', {}) \
                         .get('default', {}) \
                         .get('username', local_user)
    user = config.get('remote', {}).get('SFTP', {}).get(host, {}).get('username', default_user)
    return user
