"""
Functions for storing and retrieving cache metadata from text files.

Each Cache asset is a path: /path/filename
There are four metadata files in the cache for each:
    /path/.stagecache.filename/size    The size of the asset in bytes
    /path/.stagecache.filename/cache_lock    The requested end time of the cache
    /path/.stagecache.filename/log     A record of past requests
    /path/.stagecache.filename/write_lock
                                       Exists if cache being updated

There are also global metadata files in cache_root:
    .stagecache.global/asset_list    list of assets in this cache
    .stagecache.global/write_lock

Usage:
    Initialize TargetMetadata() class with cache_root and target paths.
    Initialize CacheMetadata() class with cache_root path

TargetMetadata Functions:
    get_cached_target_size(): returns size and date from file
    set_cached_target_size(size): writes size to file
    get_last_lock_date(): returns the most recent lock end date
    set_cache_lock_date(date): writes new date to lock file
    get_write_lock():
                        mark file as in progress (wait for existing lock)
    release_write_lock(): remove in_progress mark

CacheMetadata Functions:
    get_write_lock()
    iter_cached_files(locked=None):
                        return list of assets with sizes and lock dates
    remove_cached_file(path): remove record of asset
    add_cached_file(path): add record of asset

All functions take cache=cache_root as a kwarg
All get_ functions throw FileNotFound exception if asset not yet in cache

"""
import logging
import os
import time

def get_cached_target(cache_root, target_path):
    return os.path.abspath(cache_root + target_path)

class Lockable():
    def get_write_lock(self, sleep_interval=3):
        """ mark file as in progress (wait for existing lock) """
        while os.path.exists(self.write_lock):
            time.sleep(sleep_interval)

        with open(self.write_lock, 'wt') as LOCK:
            LOCK.write('locked')


    def release_write_lock(self):
        """ remove in_progress mark """
        os.remove(self.write_lock)

class TargetMetadata(Lockable):
    def __init__(self, cache, target_path, atype):
        self.cache_root = os.path.abspath(cache.cache_root)
        self.target_path = target_path
        self.atype = atype
        self.cached_target = get_cached_target(self.cache_root, 
                                               self.target_path,
                                              )
        cache_dir, cache_name = os.path.split(self.cached_target)
        self.md_dir = os.path.join(cache_dir, '.stagecache.' + cache_name)
        if not os.path.exists(self.md_dir):
            os.makedirs(self.md_dir)
        self.write_lock = os.path.join(self.md_dir, 'write_lock')
        logging.debug("""created TargetMetadata: 
                      cache_root=%s
                      target_path=%s
                      cached_target=%s
                      cache_dir=%s
                      md_dir=%s
                      write_lock=%s""",
                      self.cache_root, self.target_path, self.cached_target,
                      cache_dir, self.md_dir, self.write_lock)
                      

    def get_md_value(self, md_type):
        """  returns mtime of md file and int value from file """
        md_file = os.path.join(self.md_dir, md_type)
        mtime = os.path.getmtime(md_file)
        with open(md_file, 'rt') as md_handle:
            value = int(md_handle.readlines()[0].strip())
        return (value, mtime)

    def set_md_value(self, md_type, value):
        """ writes value to md file """
        md_file = os.path.join(self.md_dir, md_type)
        if os.path.exists(md_file):
            self.catalog(md_type)
        with open(md_file, 'wt') as SIZE:
            SIZE.write(str(value))

    def catalog(self, md_type):
        """ archives old md and returns value """
        log_file = os.path.join(self.md_dir, 'log')
        mtime, value = self.get_md_value(md_type)
        with open(log_file, 'at') as LOG:
            LOG.write("\t".join((
                md_type,
                str(mtime),
                time.ctime(mtime),
                str(value),
            )) + "\n")

        os.remove(log_file)
        return value

    def get_cached_target_size(self):
        """  returns size and date """
        return self.get_md_value('size')

    def set_cached_target_size(self, size):
        """ writes size to file """
        self.set_md_value('size', size)

    def get_last_lock_date(self):
        """ returns the most recent lock end date """
        return self.get_md_value('cache_lock')[0]

    def set_cache_lock_date(self, date):
        """ writes size to file """
        self.set_md_value('cache_lock', date)

    def is_lock_valid(self):
        """ checks if lock date has passed """
        return self.get_last_lock_date() > time.time()

    def remove_target(self):
        """ archive metadata for this asset """
        return self.catalog('size'), self.catalog('cache_lock')


class CacheMetadata(Lockable):
    def __init__(self, cache):
        self.cache = cache
        self.md_dir = os.path.abspath(
            os.path.join(self.cache.cache_root, '.stagecache.global')
        )
        self.write_lock = os.path.join(self.md_dir + "write_lock")
        self.asset_list = os.path.join(self.md_dir + "asset_list")

    def iter_cached_files(self, locked=None):
        """ return list of assets with sizes and lock dates """
        with open(self.asset_list) as assets:
            for asset in assets:
                # tab separated, two columns
                target_path, atype = [a.strip() for a in asset.split('\t')]
                target_metadata = TargetMetadata(self.cache, target_path, atype)
                if locked is None or target_metadata.is_lock_valid() == locked:
                    yield target_metadata

    def remove_cached_file(self, target_metadata):
        """ remove record of cached file, return size """
        with open(self.asset_list) as assets:
            asset_list = assets.readlines()
    
        count = 0
        with open(self.asset_list, 'wt') as assets:
            for asset in asset_list:
                target_path, atype = [a.strip() for a in asset.split('\t')]
                if target_path != target_metadata.target_path:
                    assets.write(asset)
                else:
                    count += 1

        if count == 0:
            logging.error("No match for " + target_path)
            raise Exception("Error recording assets")

        if count > 1:
            logging.warning("Found {} listings for {}".format(count,
                                                              target_path))

        return target_metadata.remove_target()

    def add_cached_file(self, target_metadata, target_size, lock_end_date):
        """ add record of asset """
        # add to global md
        with open(self.asset_list, 'at') as assets:
            assets.write(target_metadata.target_path + "\t" \
                          + target_metadata.atype + "\n")

        # add file specific md
        target_metadata.set_cached_target_size(target_size)
        target_metadata.set_cache_lock_date(lock_end_date)
