from argparse import Action, ArgumentParser


class InitAction(Action):
    def __init__(self, option_strings, dest, **kwargs):
        return super().__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string, **kwargs):
        from .repo import Repository
        from .filter import make_filters
        filters = make_filters()
        from .entry import PathConfig
        cfg = PathConfig()
        for f in filters:
            f.make_default_config(cfg)
        from pathlib import Path
        cfg_file = Path(Repository.CONFIG_FILENAME)
        assert not cfg_file.exists(), f'{cfg_file.as_posix()} already exists.'
        with open(cfg_file, 'wb') as f:
            from tomli_w import dump
            dump({'.': cfg}, f)
        from .logger import log
        log.info(f'An default config file is written to {cfg_file.as_posix()}')
        parser.exit()


def create_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog='rindex',
        description='Save metadata to index files',
    )
    from pathlib import Path
    parser.add_argument('src', action='store', type=str)
    parser.add_argument('dest', action='store', type=Path)
    parser.add_argument('--init',
        action=InitAction,
        help='Save a default config file in the current repository.',
        nargs=0
    )
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
