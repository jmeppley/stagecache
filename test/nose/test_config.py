import os
import yaml
from importlib import reload
from jme.stagecache import config

# create some test files
if not os.path.exists('test/.test.files'):
    os.makedirs('test/.test.files')
global_config_path = 'test/.test.files/global.config'
user_config_path = 'test/.test.files/user.config'

def check_default_config():
    dummy_root = 'test/.cache.tmp/dummy'
    c = config.get_config(dummy_root)
    assert c['cache_time'] == '1-0:00'
    assert c['cache_root'] == os.path.abspath(dummy_root)
    assert 'cache_size' not in c

def test_config_from_global():
    dummy_root = 'test/.cache.tmp'
    global_config = {
        'cache_root': dummy_root,
        'cache_size': 1e10,
    }
    user_config = {}
    with open(global_config_path, 'wt') as H:
        yaml.dump(global_config, H)
    with open(user_config_path, 'wt') as H:
        yaml.dump(user_config, H)

    # remove existing config file
    if os.path.exists(os.path.join(dummy_root,
                                   '.stagecache.global',
                                   'config')):
        os.remove(os.path.join(dummy_root, '.stagecache.global', 'config'))

    reload(config)
    config.GLOBAL_CONFIG = global_config_path
    config.USER_CONFIG = user_config_path

    c = config.get_config()
    assert c['cache_root'] == os.path.abspath(dummy_root)
    assert 'cache_size' in c
    print(c['cache_size'])
    assert c['cache_size'] == 1e10
    assert c['cache_time'] == '1-0:00'
