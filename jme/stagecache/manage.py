"""
Functions for managing and debugging a stagecache cache
"""
import os, re
from jme.stagecache.cache import Cache

def delete_enough_files(gigs_to_free, suffix=None, cache_root=None):
    """ detlete enough file to free up the requested number of GB of space

    optinally specify a suffix and only delete matching files """
    cache = Cache(cache_root)

    # assets sorted by requested lock date
    all_assets = sorted(
         cache.metadata.iter_cached_files(),
         key=lambda a: a.get_last_lock_date())

    needed_space = gigs_to_free * pow(1024,3)

    cum_sum = 0
    count = 0
    for a in all_assets:
         if suffix is None or a.cached_target.endswith(suffix):
             cum_sum += a.get_cached_target_size()[0]
             count += 0
             scache.remove_cached_file(a)
             if cum_sum > needed_space:
                 break
     
    return count 


def find_unlisted_assets(cache_root=None):
    """ Look in the configured cache to make sure all the files on disk
    are in the cache's asset_list

    returns: list of unlisted assets"""
    cache = Cache(cache_root)
    assets_on_disk = find_assets_in_dir(cache.cache_root)
    listed_assets = cache.inspect_cache()['files']
    return [a for a in assets_on_disk if a not in listed_assets]

def find_assets_in_dir(root_dir):
    for current_root, dir_list, file_list in os.walk(root_dir):
        for d in dir_list:
            if d.startswith('.stagecache.'):
                if d == '.stagecache.global':
                    continue

                if os.path.exists(os.path.join(current_root, d, 'cache_lock')):
                    yield os.path.join(current_root, d[12:])[len(root_dir):]

def guess_type(asset, root):
      local_asset = root + asset
      if os.path.exists(local_asset):
          if os.path.isfile(local_asset):
              return "file"
          else:
              if re.search('seqdbs', asset):
                  return 'taxdb'
      else:
          if os.path.basename(asset) == 'lastdb':
              return 'lastdb'
      return None
