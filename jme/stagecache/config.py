import os

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
    ## TODO:
    return {}

    
    
        

