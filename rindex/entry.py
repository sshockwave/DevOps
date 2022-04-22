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
