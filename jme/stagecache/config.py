import os
import yaml
import json

def get_conn_args():
    ## TODO:
    pass

def load_cache_config(cache_root):
    """ Load cache size and other params from config file """
    config_file = os.path.abspath(
        os.path.join(cache_root, '.stagecache.global','config')
    )

    # read config file
    cache_config = load_config(config_file)

    return cache_config
    
def load_config(config_file):
    try:
        return load_yaml_config(config_file)
    except:
        pass
    return load_json_config(config_file)

def load_yaml_config(config_file):
    with open(config_file) as config_handle:
        return yaml.load(config_handle, Loader=yaml.FullLoader)

def load_json_config(config_file):
    with open(config_file) as config_handle:
        return json.load(config_handle)
    

    
    
        

