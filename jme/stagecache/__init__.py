import re
from jme.stagecache.target import get_target
from jme.stagecache.types import asset_types
from jme.stagecache.cache import Cache

def cache_target(target_url, cache=None, atype=None, time=None):
    """
    if file not cached, copy to cache.

    return cached location
    """
    
    ## TODO: get new asset types from config
    # check config files for missing info
    cache, atype, time = fall_back_to_defaults(cache, atype, time)

    # traslate time string into seconds
    cache_time = parse_slurm_time(time)

    # initialize the Cache (turn directory name into object)
    cache = Cache(cache)

    # initialize the Target
    target = get_target(target_url, asset_types[atype])
    ## TODO: resonable error if atype not in asset list

    return cache.add_target(target, cache_time)

def fall_back_to_defaults(cache, atype, time):
    """
    Look up the default configuration and use if any of the arguments are 
    set to None
    """
    ## TODO: look in config for defaults for any of the above that are None
    return cache, atype, time

TIME_REXP = re.compile(r'(?:(\d+)-)?(\d?\d):(\d?\d)(?::(\d\d))?')
def parse_slurm_time(time):
    """
    Parse time string and add to current time

    We're using SLURM-style time strings or just seconds.
    1-0:00 is one day
    12:00 is twelve hours
    123 is 123 seconds
    0:01:23 is one minute 23 seconds
    """
    try:
        days, hours, minutes, seconds = \
                (0 if g in ["", None] else int(g) \
                 for g in TIME_REXP.search(time).groups())
        total_seconds = seconds + 60*(minutes + 60*(hours + 24*days))
    except:
        total_seconds = int(time)

    return total_seconds


