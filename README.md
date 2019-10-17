# stagecache
Stage files in a local cache.

## Overview
### Limited Storage
The primary use case for stagecache is to automatical copy files from remote or
low-performance volumes to faster local storage. This is useful when there is not
enough space in the fast/local filesystem to store all resources.

### checksums
Files are copied with rsync (over ssh for remote files) to prevent copy errors.

### lock lifetime
Files are placed in the cache with an expiration date. Until that time, other files
cannot displace them. After that time, files may be deleted if space is needed.

## installation
Simple install with conda:

    conda install -c jmeppley stagecache

Or with setup tools:

    git clone https://github.com/jmeppley/stagecache
    cd stagecache
    pip install -e $(pwd)

## Usage
The basic usage is:

    stagecache.py /path/to/file

StageCache checks to see if the file exists in the local cache, copies the file
if necessary, and returns the local path. It can be used inline:

    md5sum $(stagecache.py /path/to/file)

In this case, md5sum will be given the local path to process.

If you don't have a cache location configured (see below), it will default to ~/.cache. You can specify it explicitly with:

    stagecache.py -c /path/to/cache /path/to/file

StageCache supports some compoud file types (bwa and lastdb databases), and
more can be configured.

    lastal $(stagecache.py -a lastdb /path/to/lastdb) /path/to/query.fasta

StageCache can be run with no arguments to see the state of the cache:

    stagecache.py

## URLs

File locations can be specified as SFTP URLs:

    stagecache.py SFTP://readonly@server.com/path/to/file

You must have passwordless SSH configured for this to work. It will eventually
work with ssh-agent if it doesn't already.

## Command Line Options

The following can be configured at runtime:

 * cache location
 * length of time file is guaranteed to exist locally
 * file type

Run `stagecache.py -h` for details.

## Configuration files

Configuration files are read from (if present):
    - /etc/stagecache.d/config
    - ${HOME}/.config/stagecache/config
    - {cache_dir}/.stagecache.global/config

Files may be JSON or YAML.

The basic config values are:

    cache_root: /mnt/stagecache
    cache_size: 1.5e+12
    cache_time: 1-0:00

If the cache_size is not configured, the filesystem is queried for avaiable
free space.

The cache_time sets how long a file is guranteed to be present after it's
requested.

### Asset Types

New compound file types can be configured as follows:

    asset_types:
        my_type:
            suff_list:
                - .ext
                - .ini
        folder:
            suff_rexp: "/[^/]+$"

### Remote Resources

To reduce command line bloat, remote locations can be configured. First, you
can specify remote usernames:

    remote:
        SFTP:
            public.server.edu:
                username: readonly
            default:
                username: jmeppley

Second, you can provide path patterns that are automatically translated to
SFTP URKs. You mave have the files mounted with NFS, but rsync over SSH is more
robust. The same code could also work on a compute node without the NFS mount.

    remote:
        mappings:
            - pattern: "/mnt/(nas_[^/]+)/(.+)"
              host_repl: "\\1.hawaii.edu"
              path_repl: "/mnt/tank/\\2"

### permissions mode
By default all files in the cache are created with mode 664 (775 for directories). These are visible to all are midifiable by group members. This enables multiple users to share one cache folder.

To change the mode, you must set it in a config file (see above):

    chache_umask: 0o644
    
NB: the traditional 3 digit umask is an octal number in python, so it must be either prefixed with "0o" (as above) or passed as a quoted string (eg: "644"). 
