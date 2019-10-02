import os
from stagecache.target import get_target
from stagecache.types import asset_types

def test_get_target():
    test_file = 'stagecache.py'
    t = get_target(test_file, asset_types['file'])
    assert t.remote_path == test_file
    assert t.path_string == os.path.abspath(test_file)

    assert t.get_size() == os.path.getsize(test_file)
    assert t.get_mtime() == os.path.getmtime(test_file)

    test_url = 'SFTP://readonly@test.hawaii.edu/remote/resource/lastdb'
    t = get_target(test_url, asset_types['lastdb'])
