from typing import TypedDict, Literal
from datetime import datetime, tzinfo
from pathlib import PurePath

def sanitize_path(p: str) -> str:
    p: PurePath = PurePath(p)
    assert not p.is_absolute(
    ), f'Path "{t}" should be relative, not absolute.'
    for t in p.parts:
        assert t != '.', f'Path "{t}" cannot contain "."'
        assert t != '..', f'Path "{t}" cannot contain ".."'
    return p

class PathConfig(dict):
    # The following defaults are for the root
    # All paths inherit its config from its parent

    r"""
    Binding means using the exact same content.
    Overlay folders can modify or add extra files.
    Or you can ignore folders.

    You can set at most one option among these three.
    """
    bind: PurePath | Literal[False] = False
    overlay: PurePath | Literal[False] = False
    ignore: bool = False

    r"""
    Metadata options
    """
    timezone: tzinfo

    r"""
    If standalone, the index file is separated.
    standalone = 1: index file of the current file / folder is separated
    standalone > 1: All files within this depth should be individually indexed
    """
    standalone: int = 0

    def calc(self, rel_path: PurePath) -> 'PathConfig':
        from copy import copy
        that = copy(self)
        if self.bind is not False:
            that.bind /= rel_path
        if self.overlay is not False:
            that.overlay /= rel_path
        that.standalone = max(that.standalone - len(rel_path.parts), 0)
        return that

    def join_options(self, opt: dict):
        assert isinstance(opt, dict), f'Config "{opt}" is not a table.'
        for key, val in opt.items():
            match key:
                case 'data':
                    assert isinstance(val, dict), 'Key "data" must be a dict.'
                    options = ['plain', 'bind', 'overlay', 'ignore']
                    assert len(
                        val) == 1, f'Option "data" must contain exactly one of {",".join(options)}'
                    for o in options[1:]:
                        # Clear up current options
                        setattr(self, o, False)
                    data_key = list(val.keys())[0]
                    data_val = val[data_key]
                    match data_key:
                        case 'plain':
                            assert data_val == True
                        case 'bind':
                            assert isinstance(data_val, str)
                            self.bind = sanitize_path(data_val)
                        case 'overlay':
                            assert isinstance(data_val, str)
                            self.overlay = sanitize_path(data_val)
                        case 'ignore':
                            assert data_val == True
                            self.ignore = True
                case 'standalone':
                    if isinstance(val, bool):
                        val = 1
                    assert isinstance(val, int)
                    self.standalone = val
                case 'timezone':
                    assert isinstance(val, str)
                    self.timezone = val
                case 'save_mtime':
                    pass
                case _:
                    assert False, f'Unrecognized option: {key}'

class FileEntry(TypedDict, total=False):
    # Keys starting with '_' means that it will not appear in the final index

    # Relative path to the root when creating the base
    _ref_count: int

    size: int
    # Modified time
    mtime: datetime
    mtime_ns: int
    # Not planned: atime

    # Checksums
    crc32: str
    md5: str
    sha1: str
    sha256: str
    sha512: str


class DirEntry(TypedDict, total=False):
    _ref_count: int
    _exported: bool
