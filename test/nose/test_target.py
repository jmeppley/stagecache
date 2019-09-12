import os
from jme.stagecache.target import get_target, URL_REXP
from jme.stagecache.types import asset_types

def test_get_target():
    test_file = 'stagecache.py'
    t = get_target(test_file, asset_types['file'])
    assert t.remote_path == test_file
    assert t.path_string == os.path.abspath(test_file)

    assert t.get_size() == os.path.getsize(test_file)
    assert t.get_mtime() == os.path.getmtime(test_file)

    test_url = 'SFTP://readonly@test.hawaii.edu/remote/resource/lastdb'
    t = get_target(test_url, asset_types['lastdb'])

def test_url_rexp_1():
    m = \
        URL_REXP.search('SFTP://readonly@test.hawaii.edu/remote/resource/lastdb')
    assert m is not None

    print(m.groups())
    protocol, user, host, path = m.groups()
    assert protocol == 'SFTP'
    assert user == 'readonly'
    assert host == 'test.hawaii.edu'
    assert path.startswith('/')

def test_url_rexp_2():
    m = \
        URL_REXP.search('SFTP://test.berkeley.edu/remote/resource/lastdb')
    assert m is not None

    print(m.groups())
    protocol, user, host, path = m.groups()
    assert protocol == 'SFTP'
    assert user is None
    assert host == 'test.berkeley.edu'
    assert path.startswith('/')

def test_url_rexp_3():
    m = \
        URL_REXP.search('file:///remote/resource/lastdb')
    assert m is not None

    print(m.groups())
    protocol, user, host, path = m.groups()
    assert protocol == 'file'
    assert user is None
    assert host == ''
    assert path.startswith('/')

