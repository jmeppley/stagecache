import glob
import logging
import re
import os
import subprocess
import stat
from contextlib import contextmanager
from jme.stagecache.util import parse_url
from jme.stagecache.ssh import passwordless_sftp

LOGGER = logging.getLogger(name='target')

class EmptyTargetException(Exception):
    pass

def get_target(target_url, asset_type, config={}):
    """return appropriate target object """
    LOGGER.info("Inspecting target: {}({})".format(target_url, asset_type))

    remote = parse_url(target_url, config)

    if remote is None:
        # regular file
        return Target(target_url, asset_type)
    else:
        if remote.protocol.upper() in ['SFTP', 'SCP']:
            LOGGER.info("Target on remote host: " + remote.host)
            return SFTP_Target(remote, asset_type)
        else:
            raise Excpetion("Unsupported protocol: " + remote.protocol)

def collect_target_files(fs, target_path, asset_type):
    """
    look on fs for target files using target_path prefix and asset_type
    """

    # collect as dict to remove duplicates
    files = {}

    # collect files with explicit suffixes
    if 'suff_list' in asset_type['contents']:
        for suffix in asset_type['contents']['suff_list']:
            file_path = target_path + suffix
            LOGGER.debug("Getting mtime for " + file_path)
            try:
                stats = fs.stat(file_path)
            except:
                LOGGER.error("ERROR: getting status of: " + file_path)
                raise
            files[file_path] = {'mtime': stats.st_mtime,
                                'size': stats.st_size}


    # scan filesystem for files matching suffix regex
    if 'suff_patt' in asset_type['contents']:
        patt = asset_type['contents']['suff_patt']
        remote_dir, prefix = os.path.split(target_path)
        clip = len(prefix)
        LOGGER.debug("Getting mtime from files in {} matching {}".format(
            remote_dir,
            patt))
        for remote_file in fs.listdir(remote_dir):
            if remote_file.startswith(prefix):
                if re.search(patt, remote_file[clip:]):
                    file_path = os.path.join(remote_dir, remote_file)
                    fileattr = fs.stat(file_path)
                    if not stat.S_ISDIR(fileattr.st_mode):
                        stats = fs.stat(file_path)
                        files[file_path] = {'mtime': stats.st_mtime,
                                             'size': stats.st_size}

    # done
    return files

class Target():
    """ Represents an asset somewhere on the local filesystem """

    def __init__(self, path_string, asset_type):
        self.path_string = os.path.abspath(path_string)
        self.remote_path = path_string
        self.asset_type = asset_type

    @contextmanager
    def filesystem(self):
        yield os
        pass

    def get_target_files(self):
        # open connection to remote or use os module for local
        with self.filesystem() as fs:
            LOGGER.debug("looking for target files: {} ({})".format(
                self.remote_path, self.asset_type))

            files = collect_target_files(fs,
                                         self.remote_path,
                                         self.asset_type)

            if len(files) == 0:
                raise EmptyTargetException(
                    "Target {}({}) not found!"
                    .format(self.path_string, self.asset_type['name'])
                )

            self.mtime = max(d['mtime'] for d in files.values())
            self.size = sum(d['size'] for d in files.values())
            self.files = list(files.keys())

    def get_mtime(self):
        """
        get modification date of asset
        """
        if 'mtime' not in self.__dict__:
            self.get_target_files()

        return self.mtime

    def get_size(self):
        """
        get total size of asset
        """
        if 'size' not in self.__dict__:
            self.get_target_files()

        return self.size


    def get_remote_pref(self):
        """ empty string for local files """
        return ""

    def copy_to(self, dest_path, umask=0o664, dry_run=False):
        """ Use rsync to copy files """

        if 'files' not in self.__dict__:
            self.get_target_files()

        # for each file:
        #  rsync -lt [username@host:]remote_path cached_target_dir
        rsync_cmd_templ = 'rsync -Lt {remote_pref}{remote_file} {cached_file}'
        remote_pref = self.get_remote_pref()
        # if target is a dir, we need to adjust
        if os.path.dirname(next(iter(self.files))) == self.remote_path:
            cached_dir = dest_path
        else:
            cached_dir = os.path.dirname(dest_path)

        LOGGER.info("syncing files from " + self.remote_path)
        for remote_file in self.files:
            cached_file = os.path.join(cached_dir,
                                       os.path.basename(remote_file))
            rsync_cmd = rsync_cmd_templ.format(**locals())
            LOGGER.debug("Running: " + rsync_cmd)

            if not dry_run:
                if not os.path.exists(cached_dir):
                    os.makedirs(cached_dir)
                subprocess.run(rsync_cmd, shell=True, check=True)

                # set umask
                try:
                    os.chmod(cached_file, umask)
                except:
                    # TODO: so far this happens when other user has already created
                    # the file. We should explicitly check for this and
                    # move on if the umask is OK.
                    LOGGER.warn("Unable to set umask.")

class SFTP_Target(Target):
    """ Represents an asset somewhere on a remote filesystem """
    def __init__(self, remote, asset_type):
        super().__init__(os.path.join(remote.host, remote.path), asset_type)
        self.host = remote.host
        self.remote_path = remote.path
        self.username = remote.user

    @contextmanager
    def filesystem(self):
        LOGGER.info("Connecting to %s as %s", self.host, self.username)

        with passwordless_sftp(self.host, self.username) as sftp:
            yield sftp

                    
    def get_remote_pref(self):
        """ prefix for rsync remote path """
        return self.username + "@" + self.host + ":"

