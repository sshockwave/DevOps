from pathlib import Path, PurePath
from typing import Literal, Tuple, TypedDict, Optional
from datetime import tzinfo, datetime
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
    Metadata options
    """
    save_mtime: bool
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
                    assert isinstance(val, bool)
                    self.save_mtime = val
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
    _exported: int


def create_file_fs_entry(d: dict) -> FileEntry:
    assert isinstance(d, dict), f'Index data error.'
    val = FileEntry()
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


def pure_fs_entry(d: FileEntry) -> FileEntry:
    return {k: v for k, v in d.items() if not k.startswith('_')}


def export_fs_entry(d: FileEntry, cfg: PathConfig) -> FileEntry:
    if isinstance(cfg.timezone, str):
        import pytz
        d['mtime'] = d['mtime'].astimezone(pytz.timezone(cfg.timezone))
    else:
        d['mtime'] = d['mtime'].astimezone(cfg.timezone)
    if not cfg.save_mtime:
        del d['mtime']
        del d['mtime_ns']
    return pure_fs_entry(d)


class RepoConfig:
    def __init__(self, options: dict[str, dict]) -> None:
        from .graph import Tree
        self.config = Tree[PathConfig]()
        assert isinstance(options, dict)
        original_path: dict[PurePath, str] = dict()
        for path in options.keys():
            new_path = sanitize_path(path)
            if new_path in original_path:
                assert False, f'Path conflict: "{path}" and "{original_path[new_path]}"'
            original_path[new_path] = path
        paths = list(original_path.keys())
        paths.sort()
        self.config.val = PathConfig()
        self.config.val.standalone = 1
        self.config.val.timezone = datetime.fromtimestamp(0).astimezone().tzinfo
        self.config.val.save_mtime = True
        edges = []
        for path in paths:
            former_half, parent_node = self.config.last_value_node(path)
            if path != former_half:
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


def is_empty(path: Path):
    from os import scandir
    with scandir(path) as it:
        return not any(it)


class Repository:
    INDEX_FILENAME = 'index.toml'
    CONFIG_FILENAME = 'rindex.toml'
    FSCACHE_FILENAME = 'fscache.dat'
    repo_root: Path
    rel_root: PurePath
    dir_cache: CacheStore[PurePath, DirEntry]
    file_cache: CacheStore[PurePath, FileEntry]

    def __init__(self, root: Path) -> None:
        self.repo_root, self.rel_root = self.repo_split(root)
        assert self.repo_root is not None, f'{self.CONFIG_FILENAME} must exist for a repository.'
        with open(self.repo_root / self.CONFIG_FILENAME, 'rb') as f:
            import tomli
            self.config = RepoConfig(tomli.load(f))
        self.dir_cache = dict()
        self.file_cache = dict()
        # TODO check: whether self.rel_root contains a mapping source and dest

    def repo_split(self, path: Path) -> Tuple[Optional[Path], PurePath]:
        from os.path import abspath
        path = Path(abspath(path))
        for p in [path] + list(path.parents):
            if (p / self.CONFIG_FILENAME).is_file():
                return p, PurePath(path.relative_to(p))
        return None, path

    def open_folder(self, rel_path: PurePath):
        val: DirEntry = self.dir_cache.get(rel_path)
        if val is not None:
            val['_ref_count'] += 1
            self.dir_cache[rel_path] = val
            return
        if rel_path.parent != rel_path:
            self.open_folder(rel_path.parent)
        # Check if index file exists
        index_file = self.repo_root / rel_path / self.INDEX_FILENAME
        if index_file.exists():
            # A full scan is needed,
            # otherwise data loss can happen on config change.
            self.load_index(index_file)
        val = DirEntry()
        val['_ref_count'] = 1
        self.dir_cache[rel_path] = val

    def close_folder(self, rel_path: PurePath):
        val: DirEntry = self.dir_cache[rel_path]
        val['_ref_count'] -= 1
        if val['_ref_count'] > 0:
            self.dir_cache[rel_path] = val
            return
        if '_exported' not in val:
            self.export_folder_index(rel_path, allow_unused=True)
        abs_path = self.repo_root / rel_path
        if '_exported' not in self.dir_cache[rel_path]:
            (abs_path / self.INDEX_FILENAME).unlink(missing_ok=True)
        if abs_path.exists() and abs_path.is_dir() and is_empty(abs_path):
            abs_path.rmdir()
        del self.dir_cache[rel_path]
        if rel_path.parent != rel_path:
            self.close_folder(rel_path.parent)

    def export_folder_index(self, rel_path: PurePath, allow_unused: bool):
        if self.config[rel_path].standalone == 0:
            return
        idx_file = self.repo_root / rel_path / self.INDEX_FILENAME
        idx_file.parent.mkdir(parents=True, exist_ok=True)
        data = dict()
        for k in self.file_cache:
            if not k.is_relative_to(rel_path):
                # TODO improve speed
                continue
            v = self.file_cache[k]
            if not allow_unused and v.get('_ref_count', 0) == 0:
                continue
            data[k.relative_to(rel_path).as_posix()] = export_fs_entry(v, self.config[k])
        if len(data) > 0:
            if rel_path in self.dir_cache:
                val = self.dir_cache[rel_path]
                val['_exported'] = True
                self.dir_cache[rel_path] = val
            from .store import safe_dump
            with safe_dump(idx_file) as f:
                import tomli_w
                tomli_w.dump(data, f)
        # Safely dumped. We can remove the files from the cache now.
        to_del = []
        for k in self.file_cache:
            if not k.is_relative_to(rel_path):
                # TODO improve speed
                continue
            to_del.append(k)
        for p in to_del:
            self.close_file(p)

    def close(self):
        assert len(self.dir_cache) == 0
        assert len(self.file_cache) == 0
        del self.dir_cache
        del self.file_cache

    def open_file(self, rel_path: PurePath):
        val: FileEntry = self.file_cache.get(rel_path)
        if val is not None:
            val['_ref_count'] = val.get('_ref_count', 0) + 1
            return
        val = FileEntry()
        val['_ref_count'] = 1
        self.file_cache[rel_path] = val

    def close_file(self, rel_path: PurePath):
        val: FileEntry = self.file_cache[rel_path]
        if '_ref_count' not in self.file_cache:
            val['_ref_count'] = 0
        else:
            val['_ref_count'] -= 1
            assert val['_ref_count'] >= 0
        if val['_ref_count'] == 0:
            del self.file_cache[rel_path]

    def get_file_entry(self, rel_path: PurePath) -> Optional[FileEntry]:
        return self.file_cache.get(rel_path)

    def set_file_entry(self, rel_path: PurePath, val: FileEntry):
        if (old_val := self.file_cache.get(rel_path)) is not None:
            val['_ref_count'] = old_val.get('_ref_count', 0) + 1
        self.file_cache[rel_path] = val

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
                if self.dir_cache.get(fp, dict()).get('_ref_count', 0) == 0:
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
                if tp in self.file_cache:
                    from .logger import log
                    log.warn(f'Duplicated entry at {tp}')
                self.file_cache[tp] = create_file_fs_entry(d)

