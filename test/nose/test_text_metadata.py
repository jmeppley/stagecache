import os
import subprocess
from jme.stagecache import text_metadata
from jme.stagecache.cache import Cache

import logging
logging.basicConfig(log_level=logging.DEBUG)

def test_get_cache_dir():
    test_dir = 'test/.cache.tmp'
    test_file = 'stagecache.py'
    cd = text_metadata.get_cached_target(test_dir, os.path.abspath(test_file))
    print(cd)
    assert cd.startswith(os.path.abspath(test_dir))
    

def test_target_metadata():
    test_dir = 'test/.cache.tmp'
    test_file = 'stagecache.py'
    cache = Cache(test_dir)
    metadata = text_metadata.TargetMetadata(cache,
                                            os.path.abspath(test_file),
                                            'file'
                                           )

    print(metadata.md_dir)
    subprocess.run('rm -f ' + metadata.md_dir + "/*", shell=True) 
    print(os.path.abspath(test_dir))
    assert metadata.md_dir.startswith(os.path.abspath(test_dir))

    metadata.get_write_lock()

    assert os.path.exists(metadata.write_lock)
    assert 'write_lock' in os.listdir(metadata.md_dir)

    metadata.release_write_lock()
    assert not os.path.exists(metadata.write_lock)
    assert 'write_lock' not in os.listdir(metadata.md_dir)

    metadata.set_cache_lock_date(10000)
    print(metadata.get_last_lock_date())
    assert metadata.get_last_lock_date() == 10000
    metadata.set_cached_target_size(1000)
    size, date = metadata.get_cached_target_size()
    assert size == 1000

