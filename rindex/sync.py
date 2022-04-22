from rindex.entry import PathConfig
from .repo import FileEntry, Repository
from pathlib import Path, PurePath
from os import DirEntry
from .repo import FileEntry
from .filter import Filter
from typing import List


def stat_to_internal(info: DirEntry | Path, filters: List[Filter], cfg: PathConfig, old_index: FileEntry=None) -> FileEntry:
    ans = FileEntry()
    assert info.is_file()
    from datetime import datetime, timezone

    def to_dt(x):
        return datetime.fromtimestamp(x, tz=timezone.utc)
    stat = info.stat()
    ans['size'] = stat.st_size
    ans['mtime'] = to_dt(stat.st_mtime)
    ans['mtime_ns'] = stat.st_mtime_ns
    if old_index is None:
        file_changed = True
    else:
        file_changed = any(f.file_changed(old_index, ans) for f in filters)
    next_it = []
    for f in filters:
        flag = f.put_index(old_index, file_changed, cfg, ans)
        if flag is False:
            gen = f.parse_content(ans)
            next(gen)
            next_it.append(gen)
    if len(next_it) > 0:
        it = next_it
        with open(info.path, 'rb') as f:
            pbar = None
            if ans['size'] > 4 * 1024 * 1024:
                from tqdm import tqdm
                pbar = tqdm(total=ans['size'], unit='B', unit_scale=True,
                            unit_divisor=1024, desc=info.name)
            while len(it) > 0:
                chunk = f.read(4096)
                next_it = []
                for g in it:
                    try:
                        g.send(chunk)
                        next_it.append(g)
                    except StopIteration:
                        pass
                it = next_it
                if pbar is not None:
                    pbar.update(len(chunk))
            if pbar is not None:
                pbar.close()
    return ans


def get_cache_key(a: DirEntry):
    return f'{a.stat().st_dev},{a.inode()}'

class SyncWorker:
    repo: Repository
    def __init__(self, repo, fscache) -> None:
        self.repo = repo
        self.fscache = fscache
        from tqdm import tqdm
        self.pbar = tqdm()

    def close(self):
        self.pbar.close()

    def read_cache(self, a):
        import json
        d = self.fscache.get(get_cache_key(a))
        if d is None:
            return
        d = json.loads(d)
        v = FileEntry()
        for f in self.repo.filters:
            f.load_from_fscache(d, v)
        return v

    def write_cache(self, a, v):
        import json
        new_v = FileEntry()
        for f in self.repo.filters:
            f.export_to_fscache(v, new_v)
        self.fscache[get_cache_key(a)] = json.dumps(new_v)
    
    def handle_file(self, info: DirEntry | Path, dest: PurePath):
        self.repo.open_file(dest)
        fsentry = stat_to_internal(
            info,
            self.repo.filters,
            self.repo.config[dest],
            self.read_cache(info),
        )
        self.write_cache(info, fsentry)
        self.repo.set_file_entry(dest, fsentry)

    def sync(self, file_path: Path, dest: PurePath):
        if file_path.is_file():
            self.handle_file(file_path, dest)
            return
        assert file_path.is_dir(), f'Path "{file_path}" is neither file nor directory.'
        from os import scandir
        self.repo.open_folder(dest)
        with scandir(file_path) as it:
            for entry in it:
                repo_path = dest / entry.name
                if entry.is_file():
                    self.handle_file(entry, repo_path)
                    self.pbar.update()
                elif entry.is_dir():
                    self.repo.open_folder(repo_path)
                    self.sync(file_path / entry.name, repo_path)
                else:
                    assert False, f'Path "{entry.path}" is neither file nor directory.'
        self.repo.prune_unopened_entries(dest)
        with scandir(file_path) as it:
            for entry in it:
                if entry.is_dir():
                    self.repo.close_folder(dest / entry.name)
        self.repo.export_folder_index(dest, allow_unused=False)
        self.repo.close_folder(dest)
