import logging
import time
import os
import re
import shutil
from stagecache.text_metadata import TargetMetadata, CacheMetadata
from stagecache.target import collect_target_files
from stagecache.config import get_config
from stagecache.types import asset_types

LOGGER = logging.getLogger(name='cache')

class InsufficientSpaceError(Exception):
    pass

class Cache():
    def __init__(self, cache_root):
        LOGGER.debug("Creating class object for " + str(cache_root))
        self.config = get_config(cache_root)
        self.cache_root = self.config['cache_root']
        self.metadata = CacheMetadata(self)

    def add_target(self, target, cache_time=None, force=False, dry_run=False):
        """
        This is where the magic happens:

            * acquire lock for this file in this cache
            * check to see if it's here and up to date
            * make space if needed
            * copy if needed

        params: a Target() object defining the asset to copy
        returns: the path of the cached asset
        """

        # fall back to config if no cache lifetime supplied
        if cache_time is None:
            cache_time = self.config['cache_time']
        # convert time string to seconds
        cache_time = parse_slurm_time(cache_time)

        # get the location in cache to create
        target_metadata = TargetMetadata(self,
                                         target.path_string,
                                         target.asset_type['name'],
                                        )

        # acquire lock 
        target_metadata.get_write_lock(force=force, dry_run=dry_run)

        ## compare dates (mtimes)
        # target mtime
        target_mtime = target.get_mtime()

        try:
            # cached mtime
            cache_size, cache_mtime = \
                target_metadata.get_cached_target_size()
        except FileNotFoundError:
            cache_mtime = 0

        if cache_mtime < target_mtime:
            # cache is out of date
            self.metadata.get_write_lock(force=force, dry_run=dry_run)
            try:
                # get updated target size
                target_size = target.get_size()

                # check for and free up space
                #  raises InsufficientSpaceException if it can't
                self.free_up_cache_space(target_size, dry_run=dry_run)


                # do the copy
                target.copy_to(target_metadata.cached_target,
                               self.config['cache_umask'],
                               dry_run=dry_run,
                              )

                if not dry_run:
                    # update metadata
                    lock_end_date = int(time.time()) + cache_time
                    self.metadata.add_cached_file(target_metadata,
                                                  target_size,
                                                  lock_end_date)


            except InsufficientSpaceError as ise:
                if not dry_run:
                    target_metadata.release_write_lock()
                    self.metadata.release_write_lock()
                raise ise

            if not dry_run:
                self.metadata.release_write_lock()

        else:
            # file already in cache
            LOGGER.info("File is already in cache, updating lock")

            if not dry_run:
                # extend lock if new lock is longer
                lock_end_date = int(time.time()) + cache_time
                if target_metadata.get_last_lock_date() < lock_end_date:
                    target_metadata.set_cache_lock_date(lock_end_date)

        if not dry_run:
            target_metadata.release_write_lock()
        return target_metadata.cached_target


    def free_up_cache_space(self, size, dry_run=False):
        """
        delete old cached files
        """
        LOGGER.debug("We need %d bytes in cache", size)

        # how much space is there
        free_space = self.check_cache_space()
        LOGGER.debug("%d bytes free in cache", free_space)

        # is it enough
        if size > free_space:
            # no

            # get list of stale files
            unlocked_assets = self.metadata.iter_cached_files(locked=False)
            unlocked_assets = sorted(unlocked_assets,
                                     key=lambda a: a.get_last_lock_date(),
                                     reverse=True)

            # can we free up enough space?
            total_unlocked_size = sum(a.get_cached_target_size()[0] \
                                      for a in unlocked_assets)
            LOGGER.debug("We have %d bytes of stale files we can drop", size)
            if total_unlocked_size + free_space < size:
                raise InsufficientSpaceError("Cannot cache file. "
                                             "There is not enough space.")
            
            # start deleting stale files ...
            space_freed = 0
            files_removed = 0
            for asset in unlocked_assets:
                # delete one at a time ...
                asset_size = self.remove_cached_file(asset, dry_run=dry_run)
                LOGGER.debug("adding %d to %d", asset_size, free_space)

                # until we have enough space
                files_removed += 1
                space_freed += asset_size
                LOGGER.debug("We now have %d bytes of free space",
                              free_space + space_freed)
                if free_space + space_freed > size:
                    break

            LOGGER.info("Removed %d files to free %d bytes",
                        files_removed, space_freed)


    def remove_cached_file(self, target_metadata, dry_run=False):
        """ delete cached files from system and update metadata """
        LOGGER.info("removing %s", target_metadata.target_path)

        if dry_run:
            return target_metadata.get_cached_target_size()

        # collect file names
        target_files = collect_target_files(os,
                                            target_metadata.cached_target,
                                            asset_types[target_metadata.atype])

        # remove files
        for filename in target_files:
            os.remove(filename)

        # remove record
        return self.metadata.remove_cached_file(target_metadata)

    def inspect_cache(self, force=False, dry_run=False):
        """ return cache usage, cache availability
        and list of cached items """

        # when inspecting cache, force is a request to delete the 
        # cache write lock
        # dry_run is ignored
        if force:
            self.metadata.get_write_lock(force=True, dry_run=True)

        used_space = 0
        cached_files = []
        for target_metadata in self.metadata.iter_cached_files():
            target_size = target_metadata.get_cached_target_size()[0]
            used_space += target_size
            cached_files.append({
                'target': target_metadata.target_path,
                'size': target_size,
                'type': target_metadata.atype,
                'lock': target_metadata.get_last_lock_date() - time.time()
            })

        LOGGER.debug("%d bytes in cached used by %d files", used_space,
                      len(cached_files))
        if 'cache_size' in self.config:
            total_space = self.config['cache_size']
            free_space = total_space - used_space
            LOGGER.debug("%d of %d bytes free", free_space, total_space)
        else:
            free_space = shutil.disk_usage(self.cache_root).free
            LOGGER.debug("%d bytes free on filysystem", free_space)

        return {'used': used_space,
                'free': free_space,
                'root': self.cache_root,
                'files': cached_files}

    def check_cache_space(self):
        """ return the available space on the fs with cache """
        return self.inspect_cache()['free']

        """ original method:
        if 'cache_size' in get_config():
            used_cache_size = sum(tmd.get_cached_target_size()[0] \
                                  for tmd in self.metadata.iter_cached_files())
            return get_config()['cache_size'] - used_cache_size
        else:
            return shutil.disk_usage(self.cache_root).free
        """

TIME_REXP = re.compile(r'(?:(\d+)-)?(\d?\d):(\d?\d)(?::(\d\d))?')
def parse_slurm_time(time):
    """
    Parse time string and add to current time

    We're using SLURM-style time strings or just seconds.
    1-0:00 is one day
    12:00 is twelve hours
    123 is 123 seconds
    0:01:23 is one minute 23 seconds
    """
    try:
        days, hours, minutes, seconds = \
                (0 if g in ["", None] else int(g) \
                 for g in TIME_REXP.search(time).groups())
        total_seconds = seconds + 60*(minutes + 60*(hours + 24*days))
    except:
        total_seconds = int(time)

    return total_seconds


