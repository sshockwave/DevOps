from pathlib import Path, PurePath
from typing import Literal, Tuple, TypedDict, Optional
from datetime import datetime
from .store import CacheStore


def sanitize_path(p: str) -> str:
    p: PurePath = PurePath(p)
    assert not p.is_absolute(
    ), f'Path "{t}" should be relative, not absolute.'
    for t in p.parts:
        assert t != '.', f'Path "{t}" cannot contain "."'
        assert t != '..', f'Path "{t}" cannot contain ".."'
    return p

class PathConfig:
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
                    assert isinstance(val, bool)
                    self.standalone = val
                case _:
                    assert False, f'Unrecognized option: {key}'



class FSEntry(TypedDict, total=False):
    # Keys starting with '_' means that it will not appear in the final index

    # Relative path to the root when creating the base
    _is_file: bool
    _ref_count: int

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


def create_file_fs_entry(d: dict) -> FSEntry:
    assert isinstance(d, dict), f'Index data error.'
    val = FSEntry()
    val['_is_file'] = True
    for k, v in d.items():
        match k:
            case 'mtime':
                assert isinstance(v, datetime)
                val[k] = v
            case 'mtime_ns':
                assert isinstance(v, int)
                val[k] = v
            case 'crc32' | 'md5' | 'sha1' | 'sha256' | 'sha512':
                assert isinstance(v, str)
                val[k] = v.lower()
            case '_':
                assert False, f'Unrecognized index key: "{k}"'
    return val


def pure_fs_entry(d: FSEntry) -> FSEntry:
    return {k: v for k, v in d.items() if not k.startswith('_')}


def export_fs_entry(d: FSEntry) -> FSEntry:
    assert d['_is_file'], f'Cannot export directories.'
    return pure_fs_entry(d)


def compare_metadata(a: FSEntry, b: FSEntry):
    if a['_is_file'] != b['_is_file']:
        return False
    return pure_fs_entry(a) == pure_fs_entry(b)


class RepoConfig:
    def __init__(self, options: dict[str, dict]) -> None:
        from .graph import Tree
        self.config = Tree[PathConfig]()
        assert isinstance(options, dict)
        original_path: dict[PurePath, str] = dict()
        for path in options.keys():
            new_path = self.sanitize_path(path)
            if new_path in original_path:
                assert False, f'Path conflict: "{path}" and "{original_path[new_path]}"'
            original_path[new_path] = path
        paths = list(original_path.keys())
        paths.sort()
        self.config.val = PathConfig()
        self.config.val.standalone = 1
        edges = []
        for path in paths:
            former_half, parent_node = self.config.last_value_node(path)
            edges.append((path, former_half))
            latter_half = path.relative_to(former_half)
            # cur_node: self.config[former_half / latter_half]
            cfg = parent_node[latter_half].val = parent_node.val.calc(
                latter_half)
            opt = options[original_path[path]]
            cfg.join_options(opt)
            if v := cfg.bind:
                edges.append((v, path))
            if v := cfg.overlay:
                edges.append((v, path))
        assert self.config.val.standalone > 0, 'The root must be standalone.'
        from .graph import top_sort
        que = top_sort(paths, edges)
        assert len(que) == len(paths), 'Cycle detected in the mappings.'
        for x in que:
            cfg = self.config[x].val
            if addr := (cfg.bind or cfg.overlay):
                dest_path, dest = self.config.last_value_node(addr)
                rel_path = addr.relative_to(dest_path)
                addr = (dest.val.bind or dest_path) / rel_path
                if cfg.bind:
                    cfg.bind = addr
                elif cfg.overlay:
                    cfg.overlay = addr

    def __getitem__(self, path: PurePath):
        parent_path, parent_node = self.config.last_value_node(path)
        return parent_node.val.calc(path.relative_to(parent_path))


class Repository:
    INDEX_FILENAME = 'index.toml'
    CONFIG_FILENAME = 'rindex.toml'
    repo_root: Path
    rel_root: PurePath
    cache: CacheStore

    def __init__(self, root: Path) -> None:
        self.repo_root, self.rel_root = self.repo_split(root)
        assert self.repo_root is not None, f'{self.CONFIG_FILENAME} must exist for a repository.'
        with open(self.repo_root / self.CONFIG_FILENAME, 'rb') as f:
            import tomli
            self.config = RepoConfig(tomli.load(f))
        self.cache = dict()
        # TODO check: whether self.rel_root contains a mapping source and dest

    def repo_split(self, path: Path) -> Tuple[Optional[Path], PurePath]:
        from os.path import abspath
        path = Path(abspath(path))
        for p in [path] + list(path.parents):
            if (p / self.CONFIG_FILENAME).is_file():
                return p, PurePath(path.relative_to(p))
        return None, path

    def open_folder(self, rel_path: PurePath):
        val = self.cache.get(rel_path)
        if val is not None:
            if val['_is_file']:
                # File in old index
                # It should not have been opened
                assert val['_ref_count'] == 0
            else:
                val['_ref_count'] += 1
                self.cache[rel_path] = val
                return
        if rel_path.parent != rel_path:
            self.open_folder(rel_path.parent)
        # Check if index file exists
        index_file = self.repo_root / rel_path / self.INDEX_FILENAME
        if index_file.exists():
            # A full scan is needed,
            # otherwise data loss can happen on config change.
            self.load_index(index_file)
        val = FSEntry()
        val['_is_file'] = False
        val['_ref_count'] = 1
        self.cache[rel_path] = val

    def close_folder(self, rel_path: PurePath):
        val = self.cache[rel_path]
        val['_ref_count'] -= 1
        if val['_ref_count'] > 0:
            self.cache[rel_path] = val
            return
        if '_exported' not in val:
            self.export_folder_index(rel_path, allow_unused=True)
        del self.cache[rel_path]
        if rel_path.parent != rel_path:
            self.close_folder(rel_path.parent)

    def export_folder_index(self, rel_path: PurePath, allow_unused):
        if self.config[rel_path].standalone == 0:
            return
        if rel_path in self.cache:
            self.cache[rel_path]['_exported'] = True
        idx_file = self.repo_root / rel_path / self.INDEX_FILENAME
        idx_file.parent.mkdir(parents=True, exist_ok=True)
        data = dict()
        for k in self.cache:
            if k == rel_path:
                continue
            if not k.is_relative_to(rel_path):
                # TODO improve speed
                continue
            v = self.cache[k]
            if not allow_unused and v.get('_ref_count', 0) == 0:
                continue
            data[k.as_posix()] = export_fs_entry(v)
        if len(data) == 0:
            idx_file.unlink(missing_ok=True)
            # TODO Remove folder if empty
        else:
            from .store import safe_dump
            with safe_dump(idx_file) as f:
                import tomli_w
                tomli_w.dump(data, f)
        # Safely dumped. We can remove the files from the cache now.
        to_del = []
        for k in self.cache:
            if k == rel_path:
                continue
            if not k.is_relative_to(rel_path):
                # TODO improve speed
                continue
            to_del.append(k)
        for p in to_del:
            self.close_file(p)

    def close(self):
        assert len(self.cache) == 0
        del self.cache

    def open_file(self, rel_path: PurePath):
        val = self.cache.get(rel_path)
        if val is not None:
            assert val['_is_file']
            val['_ref_count'] = val.get('_ref_count', 0) + 1
            return
        val = FSEntry()
        val['_ref_count'] = 1
        self.cache[rel_path] = val

    def close_file(self, rel_path: PurePath):
        val = self.cache[rel_path]
        assert val['_is_file']
        if '_ref_count' not in self.cache:
            val['_ref_count'] = 0
        else:
            assert val['_ref_count'] >= 0
            val['_ref_count'] -= 1
        if val['_ref_count'] == 0:
            del self.cache[rel_path]

    def get_file_entry(self, rel_path: PurePath) -> Optional[FSEntry]:
        return self.cache.get(rel_path)

    def set_file_entry(self, rel_path: PurePath, val: FSEntry):
        if (old_val := self.cache.get(rel_path)) is not None:
            val['_ref_count'] = old_val.get('_ref_count', 0) + 1
        self.cache[rel_path] = val

    def prune_unopened_entries(self, rel_path: PurePath):
        from os import scandir
        work_dir = self.repo_root / rel_path
        if not work_dir.exists():
            return
        with scandir(self.repo_root / rel_path) as it:
            for entry in it:
                if entry.is_file():
                    continue
                fp = rel_path / entry.name
                assert entry.is_dir(), f'Path {fp} is neither a file or a directory'
                if fp not in self.cache or self.cache[fp].get('_ref_count', 0) == 0:
                    from shutil import rmtree
                    rmtree(entry.path)

    def load_index(self, idx_file: Path) -> None:
        assert idx_file.is_file(), f'Index "{idx_file}" exists but is not a file.'
        rel_path = idx_file.parent.relative_to(self.repo_root)
        with open(idx_file, 'rb') as f:
            import tomli
            data = tomli.load(f)
            assert isinstance(data, dict), f'Index file on "{rel_path}" is not a dict.'
            for p, d in data.items():
                assert isinstance(d, dict), f'Index file error.'
                tp = rel_path / p
                assert tp not in self.cache, f'Duplicated entry in {tp}'
                self.cache[tp] = create_file_fs_entry(d)

