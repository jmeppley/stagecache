import time
import os
from jme.stagecache.text_metadata import TargetMetadata, CacheMetadata
from jme.stagecache.config import load_cache_config

class Cache():
    def __init__(self, cache_root):
        self.cache_root = os.path.abspath(cache_root)
        self.config = load_cache_config(self.cache_root)
        self.metadata = CacheMetadata(self)

    def add_target(self, target, cache_time):
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
        target_metadata = TargetMetadata(self.cache_root, target.path_string)

        # acquire lock 
        target_metadata.get_write_lock()

        ## compare dates (mtimes)
        # target mtime
        target_mtime = target.get_mtime()

        try:
            # cached mtime
            cache_size, cache_time = \
                target_metadata.get_cached_target_size()
        except FileNotFoundException:
            cache_time = 0

        if cache_time < target_mtime:
            # cache is out of date
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


            except InsufficientSpaceException as ise:
                metadata.release_write_lock()
                raise ise


        return metadata.cached_target


    def free_up_cache_space(self, size):
        """
        delete old cached files
        """

        # how much space is there
        free_space = check_cache_space(cache)

        # is it enough
        if size > free_space:
            # no

            unlocked_assets = self.metadata.iter_cached_files(locked=False)
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


