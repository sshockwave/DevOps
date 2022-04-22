# rindex

A file indexing tool that creates a single source of truth for your personal files.
It has a command line interface similar to `rsync`, but only syncs metadata.

_Caution:_ This is **NOT** a backup tool.

Since it only reads metadata,
it follows all symlinks.

## Features

* Pure text storage of metadata: modtime, checksum, ...
* Fast rebuild based on local filesystem cache.

### Files

* Only `rindex.toml` should be handwritten.
Anything else is automatically created.
* The index files are named `index.toml`.
* Anything ending with `.dat` can be deleted / ignored from git repo.

See [`repo.py`](rindex/repo.py) for a list of files that will be created.

## Configuration
This is the default config if not specified.
```toml
["path/to/some/file"]
# If standalone, the indices of the current folder
# and subfolders are stored in a separate file
# under `path/to/some/file/index.toml`.
# standalone = 1: index file of the current file / folder is separated
# standalone > 1: All files within this depth should be individually indexed
standalone = 0
# Toggle metadata store with save_<name>
save_size=true
save_mtime=true
save_mtime_ns=false
# Timezone is used for time-related metadata.
# It defaults to the local timezone on your machine.
# See https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
timezone="Africa/Abidjan"
# sha256 is the default checksum method
# and all others are disabled by default.
# All available checksums:
# crc32, md5, sha1, sha256, sha512
save_sha256=true
```

## Contributions
Contributions are welcome in any form!
