import glob
import logging
import re
import os
import subprocess
from contextlib import contextmanager

URL_REXP = re.compile(r'^([A-Za-z]+)://(?:([^/@]+)@)?([^/]*)(/.+)$')

def get_target(target_url, asset_type):
    """return appropriate target object """
    ## TODO: allow for user from config
    match = URL_REXP.search(target_url)
    if match:
        protocol, user, host, remote_path = match.groups()
        if protocol.upper() in ['SFTP', 'SCP']:
            return SFTP_Target(host, user, remote_path, asset_type)
        if protocol.lower == 'file':
            if len(host) > 0:
                raise Exception("file URL should have no host name")
            return Target(remote_path, asset_type)
        else:
            raise Excpetion("Unsupported protocol: " + protocol)

    # we ge here if there was no match or a file:/// url
    return Target(target_url, asset_type)

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
            stats = fs.stat(file_path)
            files[file_path] = {'mtime': stats.st_mtime,
                                'size': stats.st_size}


    # scan filesystem for files matching suffix regex
    if 'suff_patt' in asset_type['contents']:
        patt = asset_type['contents']['suff_patt']
        remote_dir, prefix = os.path.split(target_path)
        clip = len(prefix)
        for remote_file in fs.listdir(remote_dir):
            if remote_file.startswith(prefix):
                if re.search(patt, remote_file[clip:]):
                    file_path = os.path.join(remote_dir, remote_file)
                    if fs.isfile(file_path):
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

            files = collect_target_files(fs,
                                         self.remote_path,
                                         self.asset_type)

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

    def copy_to(self, dest_path):
        """ Use rsync to copy files """
        if 'files' not in self.__dict__:
            self.get_target_files()

        # for each file:
        #  rsync -lt [username@host:]remote_path cached_target_dir
        rsync_cmd_templ = 'rsync -lt {remote_pref}{remote_file} {cached_file}'
        remote_pref = self.get_remote_pref()
        # if target is a dir, we need to adjust
        if os.path.dirname(next(iter(self.files))) == self.remote_path:
            cached_dir = dest_path
        else:
            cached_dir = os.path.dirname(dest_path)
        if not os.path.exists(cached_dir):
            os.makedirs(cached_dir)

        logging.info("syncing files from " + self.remote_path)
        for remote_file in self.files:
            cached_file = os.path.join(cached_dir,
                                       os.path.basename(remote_file))
            rsync_cmd = rsync_cmd_templ.format(**locals())
            logging.debug("Running: " + rsync_cmd)
            subprocess.run(rsync_cmd, shell=True, check=True)


class SFTP_Target(Target):
    """ Represents an asset somewhere on a remote filesystem """
    def __init__(self, host, user, remote_path, asset_type):
        self.host = host
        self.path_string = os.path.join(host, remote_path)
        self.remote_path = remote_path
        self.asset_type = asset_type
        self.username = user

    @contextmanager
    def filesystem(self):
        import pysftp
        kwargs = {'username': self.username,
                  'host': self.host}
        sftp_connection = pysftp.Connection(**kwargs)
        yield sftp_connection
        sftp_connection.close()


    def get_remote_pref(self):
        """ prefix for rsync remote path """
        return self.username + "@" + self.host + ":"


