from argparse import ArgumentParser


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='rindex',
        description='Save metadata to index files',
    )
    from pathlib import Path
    parser.add_argument('src', action='store', type=str)
    parser.add_argument('dest', action='store', type=Path)
    return parser


def main(args=None):
    if args is None:
        args = create_parser().parse_args()
    from .repo import Repository
    r = Repository(args.dest)
    from .sync import SyncWorker
    import dbm
    import os
    with dbm.open(os.path.join(*r.repo_root.parts, r.FSCACHE_FILENAME), flag='c') as fscache:
        w = SyncWorker(r, fscache)
        from pathlib import Path
        w.sync(Path(args.src), r.rel_root)
        w.close()
    r.close()
