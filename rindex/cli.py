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
    w = SyncWorker(r)
    from pathlib import Path
    w.sync(Path(args.src), r.rel_root)
    w.close()
    r.close()
