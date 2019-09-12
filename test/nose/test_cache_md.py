import os
import time
from jme.stagecache.types import asset_types
from jme.stagecache.cache import Cache
from jme.stagecache.target import Target
from jme.stagecache.text_metadata import CacheMetadata, TargetMetadata

import logging
logging.basicConfig(log_level=logging.DEBUG)

def test_cache_md():
    test_dir = 'test/.cache.tmp'
    cache = Cache(test_dir)
    md = CacheMetadata(cache)
    print(md.write_lock)
    print(md.asset_list)

    assert md.cache.cache_root.startswith(os.path.abspath(os.path.curdir))

    # clean up from earlier tests
    if os.path.exists(md.asset_list):
        os.remove(md.asset_list)
    if os.path.exists(md.write_lock):
        os.remove(md.write_lock)

    md.get_write_lock()
    assert os.path.exists(md.write_lock)
    md.release_write_lock()
    assert not os.path.exists(md.write_lock)

    
    t1 = Target('/some/path/1.txt', asset_types['file'])
    t2 = Target('/some/path/2.txt', asset_types['file'])
    tm1 = TargetMetadata(cache, t1.path_string, 'file')
    tm2 = TargetMetadata(cache, t2.path_string, 'file')

    md.add_cached_file(tm1, 10, int(time.time()) + 0)
    md.add_cached_file(tm2, 20, int(time.time()) + 10000000)

    cache_list = list(md.iter_cached_files())
    assert len(cache_list) == 2

    cache_list = list(md.iter_cached_files(locked=False))
    assert len(cache_list) == 1
    cache_list = list(md.iter_cached_files(locked=True))
    assert len(cache_list) == 1

    md.remove_cached_file(tm1)

    cache_list = list(md.iter_cached_files())
    assert len(cache_list) == 1
    cache_list = list(md.iter_cached_files(locked=False))
    assert len(cache_list) == 0
    cache_list = list(md.iter_cached_files(locked=True))
    assert len(cache_list) == 1

