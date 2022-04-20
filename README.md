# rindex

A file indexing tool that creates a single source of truth for your personal files.
It has a command line interface similar to `rsync`, but only syncs metadata.

_Caution:_ This is **NOT** a backup tool.

Since it only reads metadata,
it follows all symlinks.

## Features

* Pure text storage of metadata: modtime, checksum, ...
* Fast rebuild based on local filesystem cache.

### Roadmap

* Content checksums of images and audios (ignoring ID3, EXIF, etc.)
* Suggestions for problematic filenames (long file names, invalid encoding, special characters, etc.)
* Symlink-like concept inside the repo using `mapping` and `overlay`.
* Recover files from the index using another source.

### Files

* Only `rindex.toml` should be handwritten.
Anything else is automatically created.
* The index files are named `index.toml`.
* Anything ending with `.dat` can be deleted / ignored from git repo.

See [`repo.py`](rindex/repo.py) for a list of files that will be created.

## Motivations

1. I hate bit rots.
They don't happen that often on steady drives,
but SSDs fail over time, non-ECC memory has bit flips,
and network connections are unstable.
2. `ZFS`, `Btrfs`, and `S3` storage systems have built-in checksums,
but the checksum data are hard to read and export.
The files locked in to the solution.
If I get a file from another source and I would like to validate it,
I have to run `diff` or compute its checksum all over again.
3. `git` and `git-annex` are great,
but I don't trust checksums-addressed storage on my personal files.
Checksums are totally fine for detection of corruption, however.
The performance on large number of files is also a serious issue.
4. `rclone` [modifies your filename](https://rclone.org/overview/#restricted-filenames),
which is an unfortunate necessity.
I want to be notified whenever it takes place.
5. A separate list of files let me know which files I can trust
during data recovery.
6. BitTorrent is great.
You can save large files on a cheap medium,
and correct the corruptions if there are any seeders.
The downside is that it's immutable.
Not very convenient for personal use.

## Contributions
Contributions are welcome in any form!
