import re
import logging
from stagecache.target import get_target
from stagecache.types import asset_types
from stagecache.cache import Cache
from stagecache.config import get_config

LOGGER = logging.getLogger(name='main')

def cache_target(target_url, cache=None, atype=None, time=None, **kwargs):
    """
    if file not cached, copy to cache.

    return cached location
    """

    LOGGER.debug("Starting up: c=%s, a=%s, t=%s",
                  cache, atype, time)

    # initialize the Cache (turn directory name into object)
    cache = Cache(cache)

    # initialize the Target
    if atype is None:
        atype = 'file'
    target = get_target(target_url, asset_types[atype], cache.config)
    ## TODO: resonable error if atype not in asset list

    return cache.add_target(target, cache_time=time, **kwargs)

def query_cache(**kwargs):
    """ return state of cache:
        total space used
        free space

    """
    cache = kwargs.get('cache', None)
    return Cache(cache).inspect_cache(**kwargs)
