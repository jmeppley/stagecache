from jme.stagecache.util import path_up_to_wildcard, URL_REXP

def test_path_up_to_wildcard():
    " should return last full dir name before first bracket "
    assert path_up_to_wildcard('/mnt/server/volume/project/file.{suffix}') \
            == '/mnt/server/volume/project'
    assert path_up_to_wildcard('/path/to/data/{sample}/file.{type}.ext') \
            == '/path/to/data'
    assert path_up_to_wildcard('/simple/path/file.ext') \
            == '/simple/path/file.ext'


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

