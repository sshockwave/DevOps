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


## Contributions
Contributions are welcome in any form!
