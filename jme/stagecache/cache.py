import logging
import time
import os
import shutil
from jme.stagecache.text_metadata import TargetMetadata, CacheMetadata
from jme.stagecache.config import load_cache_config

class InsufficientSpaceError(Exception):
    pass

class Cache():
    def __init__(self, cache_root):
        self.cache_root = os.path.abspath(cache_root)
        self.config = load_cache_config(self.cache_root)
        self.metadata = CacheMetadata(self)

    def add_target(self, target, cache_time, force=False):
        """
        This is where the magic happens:

            * acquire lock for this file in this cache
            * check to see if it's here and up to date
            * make space if needed
            * copy if needed

        params: a Target() object defining the asset to copy
        returns: the path of the cached asset
        """

        # get the location in cache to create
        target_metadata = TargetMetadata(self,
                                         target.path_string,
                                         target.asset_type['name'],
                                        )

        # acquire lock 
        target_metadata.get_write_lock(force=force)

        ## compare dates (mtimes)
        # target mtime
        target_mtime = target.get_mtime()

        try:
            # cached mtime
            cache_size, cache_time = \
                target_metadata.get_cached_target_size()
        except FileNotFoundError:
            cache_time = 0

        if cache_time < target_mtime:
            # cache is out of date
            self.metadata.get_write_lock(force=force)
            try:
                # get updated target size
                target_size = target.get_size()

                # check for and free up space
                #  raises InsufficientSpaceException if it can't
                self.free_up_cache_space(target_size)

                # do the copy
                target.copy_to(target_metadata.cached_target)

                # update metadata
                lock_end_date = int(time.time()) + cache_time
                self.metadata.add_cached_file(target_metadata,
                                              target_size,
                                              lock_end_date)


            except InsufficientSpaceError as ise:
                target_metadata.release_write_lock()
                self.metadata.release_write_lock()
                raise ise


            self.metadata.release_write_lock()

        else:
            # file already in cache
            logging.info("File is already in cache, updating lock")

            # extend lock if new lock is longer
            lock_end_date = int(time.time()) + cache_time
            if target_metadata.get_last_lock_date() < lock_end_date:
                target_metadata.set_cache_lock_date(lock_end_date)

        target_metadata.release_write_lock()
        return target_metadata.cached_target


    def free_up_cache_space(self, size):
        """
        delete old cached files
        """

        # how much space is there
        free_space = self.check_cache_space()

        # is it enough
        if size > free_space:
            # no

            # get list of stale files
            unlocked_assets = self.metadata.iter_cached_files(locked=False)

            # can we free up enough space?
            total_unlocked_size = sum(a.get_cached_target_size() \
                                      for a in unlocked_assets)
            if total_unlocked_size + free_space < size:
                raise InsufficientSpaceError("Cannot cache file. "
                                             "There is not enough space.")
            
            # start deleting stale files ...
            for asset in sorted(unlocked_assets,
                                key=lambda a: a.get_last_lock_date(),
                                reverse=True):

                # delete one at a time ...
                asset_size = self.remove_cached_file(asset)

                # until we have enough space
                free_space += asset_size
                if free_space > size:
                    break


    def remove_cached_file(target_metadata):
        """ delete cached files from system and update metadata """
        # collect file names
        target_files = collect_target_files(os,
                                            target_metadata.cached_target,
                                            asset_types[target_metadata.atype])

        # remove files
        for filename in target_files:
            os.remove(filename)

        # remove record
        return self.metadata.remove_cached_file(asset)


    def check_cache_space(self):
        """ return the available space on the fs with cache """

        if 'cache_size' in self.config: 
            used_cache_size = [tmd.get_cached_target_size() \
                               for tmd in self.metadata.iter_cached_files()]
            return self.config['cache_size'] - used_cached_size
        else:
            return shutil.disk_usage(self.cache_root).free

