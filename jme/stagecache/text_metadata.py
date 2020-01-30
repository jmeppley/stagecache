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
import stat
from contextlib import contextmanager

LOGGER = logging.getLogger(name='metadata')

def get_cached_target(cache_root, target_path):
    return os.path.abspath(cache_root + target_path)

def makedirs(path, mode=509):
    if not os.path.exists(path):
        makedirs(os.path.dirname(path), mode)
        os.mkdir(path)
        os.chmod(path, mode=mode)

class Lockable():
    def __init__(self, cache):
        self.umask = cache.config['cache_umask']
        self.umask_dir = self.umask + 0o111

    @contextmanager
    def lock(self, sleep_interval=3, force=False, dry_run=False):
        """
        Aquire and relase lock as a context manager.
        EG:
        with target.lock():
            ...
        
        see get_write_lock for arguments
        """
        try:
            self.get_write_lock(sleep_interval, force, dry_run)
            yield None
            LOGGER.debug('Done with lock...')
        finally:
            # only release lock if it was NOT a dry run
            if not dry_run:
                self.release_write_lock()

    def get_write_lock(self, sleep_interval=3, force=False, dry_run=False):
        """ mark file as in progress (wait for existing lock) """
        LOGGER.debug('Creating lock...')
        if os.path.exists(self.write_lock):
            if force:
                os.remove(self.write_lock)
            if dry_run:
                return
            LOGGER.info('Waiting for lock...')
            LOGGER.debug("force is "+ str(force))
            while os.path.exists(self.write_lock):
                time.sleep(sleep_interval)

        if dry_run:
            return
        with open(self.write_lock, 'wt') as LOCK:
            LOCK.write('locked')
        os.chmod(self.write_lock, self.umask)

    def release_write_lock(self):
        """ remove in_progress mark """
        LOGGER.debug('Releasing lock (%s)...', self.write_lock)
        try: 
            os.remove(self.write_lock)
        except:
            pass

class TargetMetadata(Lockable):
    def __init__(self, cache, target_path, atype):
        super().__init__(cache)
        self.cache_root = os.path.abspath(cache.cache_root)
        self.target_path = target_path
        self.atype = atype
        self.cached_target = get_cached_target(self.cache_root, 
                                               self.target_path,
                                              )
        cache_dir, cache_name = os.path.split(self.cached_target)
        self.md_dir = os.path.join(cache_dir, '.stagecache.' + cache_name)
        if not os.path.exists(self.md_dir):
            makedirs(self.md_dir, mode=self.umask_dir)
        self.write_lock = os.path.join(self.md_dir, 'write_lock')
        LOGGER.debug("""created TargetMetadata: 
                      cache_root=%s
                      target_path=%s
                      cached_target=%s
                      cache_dir=%s
                      md_dir=%s
                      write_lock=%s""",
                      self.cache_root, self.target_path, self.cached_target,
                      cache_dir, self.md_dir, self.write_lock)
                      

    def get_md_value(self, md_type, delete=False):
        """  returns mtime of md file and int value from file """
        md_file = os.path.join(self.md_dir, md_type)
        if not os.path.exists(md_file):
            # file not in cache!
            return (0, None)
        mtime = os.path.getmtime(md_file)
        with open(md_file, 'rt') as md_handle:
            value = int(md_handle.readlines()[0].strip())
        if delete:
            os.remove(md_file)
        return value, mtime

    def set_md_value(self, md_type, value):
        """ writes value to md file """
        md_file = os.path.join(self.md_dir, md_type)
        if os.path.exists(md_file):
            self.catalog(md_type)
        with open(md_file, 'wt') as SIZE:
            SIZE.write(str(int(value)))
        os.chmod(md_file, self.umask)

    def catalog(self, md_type):
        """ archives old md and returns value """
        log_file = os.path.join(self.md_dir, 'log')
        value, mtime = self.get_md_value(md_type, delete=True)
        with open(log_file, 'at') as LOG:
            LOG.write("\t".join((
                md_type,
                str(mtime),
                time.ctime(mtime),
                str(value),
            )) + "\n")
        os.chmod(log_file, self.umask)

        return value

    def get_cached_target_size(self):
        """  returns size and date """
        return self.get_md_value('size')

    def set_cached_target_size(self, size):
        """ writes size to file """
        self.set_md_value('size', size)

    def get_last_lock_date(self):
        """ returns the most recent lock end date """
        lock_date = self.get_md_value('cache_lock')[0]
        return lock_date

    def set_cache_lock_date(self, date):
        """ writes new expiration date to file """
        self.set_md_value('cache_lock', date)

    def is_lock_valid(self):
        """ checks if lock date has passed """
        lock_date = self.get_last_lock_date()
        return lock_date > time.time()

    def remove_target(self):
        """ archive metadata for this asset """
        self.catalog('cache_lock')
        return self.catalog('size')


class CacheMetadata(Lockable):
    def __init__(self, cache):
        super().__init__(cache)
        self.cache = cache
        self.md_dir = os.path.abspath(
            os.path.join(self.cache.cache_root, '.stagecache.global')
        )
        self.write_lock = os.path.join(self.md_dir, "write_lock")
        self.asset_list = os.path.join(self.md_dir, "asset_list")
        if not os.path.exists(self.md_dir):
            makedirs(self.md_dir, self.umask_dir)
        LOGGER.debug("""created CacheMetadata: 
                      cache_root=%s
                      md_dir=%s
                      write_lock=%s""",
                      self.cache.cache_root, self.md_dir, self.write_lock)


    def iter_cached_files(self, locked=None):
        """ return list of assets with sizes and lock dates """
        LOGGER.debug("Checking asset list: %s", self.asset_list)
        for target_path, atype in self.list_assets():
            target_metadata = TargetMetadata(self.cache,
                                             target_path,
                                             atype)
            if locked is None  or target_metadata.is_lock_valid() == locked:
                yield target_metadata

    def list_assets(self):
        """ return list of path, type tuples in cache """
        LOGGER.debug("Fetching asset list: %s", self.asset_list)
        if os.path.exists(self.asset_list):
            asset_list = list()
            with open(self.asset_list) as assets:
                for asset_line in assets:
                    asset_line = asset_line.strip()
                    if len(asset_line) == 0:
                        continue
                    asset = tuple(a.strip() for a in asset_line.split('\t'))
                    if len(asset) != 2:
                        raise Exception("Asset tuple is NOT length 2!\n%r" % (asset,))
                    asset_list.append(asset)

            LOGGER.debug("Found %d assets in %s",
                         len(asset_list),
                         self.asset_list,
                        )
            return asset_list
        else:
            return []


    def remove_cached_file(self, target_metadata):
        """ remove record of cached file, return size """
        count = 0
        # read asset list
        asset_list = self.list_assets()
        # write new (edited) asset list
        with open(self.asset_list, 'wt') as assets:
            for target_path, atype in asset_list:
                if target_path != target_metadata.target_path:
                    assets.write(target_path + "\t" + atype + "\n")
                else:
                    count += 1
        os.chmod(self.asset_list, self.umask)

        if count == 0:
            LOGGER.error("No match for " + target_metadata.target_path)
            raise Exception("Error recording assets")

        if count > 1:
            LOGGER.warning("Found {} listings for {}".format(count,
                                                 target_metadata.target_path))

        return target_metadata.remove_target()

    def add_cached_file(self, target_metadata, target_size, lock_end_date):
        """ add record of asset """
        # add to global md
        paths_in_cache = set(a[0] for a in self.list_assets())
        if target_metadata.target_path not in paths_in_cache:
            LOGGER.debug("%s not in %s, adding...",
                         target_metadata.target_path,
                         paths_in_cache)
            # add to list if not there yet
            with open(self.asset_list, 'at') as assets:
                assets.write(target_metadata.target_path + "\t" \
                              + target_metadata.atype + "\n")
            os.chmod(self.asset_list, self.umask)
        else:
            LOGGER.debug("%s alread in asset list",
                         target_metadata.target_path)

        # add file specific md
        target_metadata.set_cached_target_size(target_size)
        target_metadata.set_cache_lock_date(lock_end_date)
