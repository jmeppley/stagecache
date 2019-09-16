import re
import logging
from jme.stagecache.target import get_target
from jme.stagecache.types import asset_types
from jme.stagecache.cache import Cache
from jme.stagecache.config import get_config

def cache_target(target_url, cache=None, atype=None, time=None, force=False):
    """
    if file not cached, copy to cache.

    return cached location
    """

    logging.debug("Starting up: c=%s, a=%s, t=%s, f=%s",
                  cache, atype, time, force)

    # initialize the Cache (turn directory name into object)
    cache = Cache(cache)

    # initialize the Target
    if atype is None:
        atype = 'file'
    target = get_target(target_url, asset_types[atype])
    ## TODO: resonable error if atype not in asset list

    return cache.add_target(target, cache_time=time, force=force)

def query_cache(**kwargs):
    """ return state of cache:
        total space used
        free space

    """
    cache = kwargs.get('cache', None)
    return Cache(cache).inspect_cache()
