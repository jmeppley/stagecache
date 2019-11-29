import logging
import time
import os
import re
import shutil
from jme.stagecache.text_metadata import TargetMetadata, CacheMetadata
from jme.stagecache.target import collect_target_files
from jme.stagecache.config import get_config
from jme.stagecache.types import asset_types
from jme.stagecache.util import get_time_string

LOGGER = logging.getLogger(name='cache')

class InsufficientSpaceError(Exception):
    pass

class Cache():
    def __init__(self, cache_root):
        LOGGER.debug("Creating class object for " + str(cache_root))
        self.config = get_config(cache_root)
        self.cache_root = self.config['cache_root']
        self.metadata = CacheMetadata(self)

    def add_target(self, target,
                   cache_time=None,
                   force=False,
                   purge=False,
                   dry_run=False):
        """
        This is where the magic happens:

            * acquire lock for this file in this cache
            * check to see if it's here and up to date
            * make space if needed
            * copy if needed

        params: a Target() object defining the asset to copy
        optional kwargs:
            cache_time: lifetime of file in cache
            force: ignore and delete any old locks, re-copy remote files
            purge: delete file if cache_time is negative and force is set
            dry_run: don't do anything (except delete locks)
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

        if cache_time < 0:
            if force:
                if purge:
                    self.remove_cached_file(target_metadata, dry_run)
                    return target_metadata.cached_target
            else:
                LOGGER.error("Use --force to remove file from cache")
                raise Exception("Cannot set negative expiration without "
                                "--force")
        elif purge:
            LOGGER.error("Use --force and --time -1 with --purge to remove a "
                         "file")
            raise Exception("Cannot purge without setting time to negative "
                            "values")

        # acquire lock
        with target_metadata.lock(force=force, dry_run=dry_run):

            ## compare dates (mtimes) of original and cached verions
            try:
                # cached mtime
                cache_size, cache_mtime = \
                    target_metadata.get_cached_target_size()
            except FileNotFoundError:
                cache_mtime = 0

            # target original mtime
            target_mtime = target.get_mtime()

            if force or cache_mtime < target_mtime:
                # cache is out of date

                with self.metadata.lock(force=force, dry_run=dry_run):
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


            else:
                # file already in cache, update lock
                # extend lock if new lock is longer
                lock_end_date = int(time.time()) + cache_time

                if force or target_metadata.get_last_lock_date() < lock_end_date:
                    LOGGER.info("File is already in cache, "
                                "updating expiration to %s.",
                                get_time_string(lock_end_date))
                    if not dry_run:
                        target_metadata.set_cache_lock_date(lock_end_date)
                else:
                    LOGGER.warning("File is already in cache with a later "
                                "expiration date, "
                                "use --force to change")

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

    def inspect_cache(self, force=False, dry_run=False, purge=False, **kwargs):
        """ return cache usage, cache availability
        and list of cached items

        if purge: remove expired files
        """

        # when inspecting cache, force is a request to delete the
        # cache write lock
        # dry_run is ignored
        if force:
            # the following deletes the lock and does not make a new one
            self.metadata.get_write_lock(force=True, dry_run=True)

        used_space = 0
        cached_files = {}
        for target_metadata in self.metadata.iter_cached_files():
            target_size = target_metadata.get_cached_target_size()[0]
            used_space += target_size
            target = target_metadata.target_path
            if target in cached_files:
                continue
            lock_date = target_metadata.get_last_lock_date()
            now = time.time()
            if purge and lock_date < now:
                self.remove_cached_file(target_metadata, dry_run)
                if dry_run:
                    lock_date = '<to-be-purged>'
                else:
                    lock_date = '<purged>'
            cached_files[target] = {
                'size': target_size,
                'type': target_metadata.atype,
                'lock': lock_date,
            }

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


