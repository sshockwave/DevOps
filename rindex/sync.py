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
    if not file_changed:
        for i in old_index:
            ans[i] = old_index[i]
    else:
        it = [f.parse_content(ans) for f in filters]
        next_it = []
        for f in it:
            try:
                next(f)
                next_it.append(f)
            except StopIteration:
                pass
        it = next_it
        with open(info.path, 'rb') as f:
            pbar = None
            if ans['size'] > 4 * 1024 * 1024:
                from tqdm import tqdm
                pbar = tqdm(total=ans['size'], unit='B', unit_scale=True,
                            unit_divisor=1024, desc=info.name)
            while chunk := f.read(4096):
                next_it = []
                for f in it:
                    try:
                        f.send(chunk)
                        next_it.append(f)
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
        if 'mtime' in d:
            from datetime import datetime
            d['mtime'] = datetime.fromisoformat(d['mtime'])
        return d

    def write_cache(self, a, v):
        import json
        from copy import copy
        v = copy(v)
        if 'mtime' in v:
            v['mtime'] = v['mtime'].isoformat()
        self.fscache[get_cache_key(a)] = json.dumps(v)

    def sync(self, file_path: Path, dest: PurePath):
        if file_path.is_file():
            self.repo.set_file_entry(dest, stat_to_internal(file_path))
            return
        assert file_path.is_dir(), f'Path "{file_path}" is neither file nor directory.'
        from os import scandir
        self.repo.open_folder(dest)
        with scandir(file_path) as it:
            for entry in it:
                repo_path = dest / entry.name
                if entry.is_file():
                    self.repo.open_file(repo_path)
                    fsentry = stat_to_internal(
                        entry,
                        self.repo.filters,
                        self.repo.config[repo_path],
                        self.read_cache(entry),
                    )
                    from .repo import pure_fs_entry
                    self.write_cache(entry, pure_fs_entry(fsentry))
                    self.repo.set_file_entry(repo_path, fsentry)
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
