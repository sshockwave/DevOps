from .repo import Repository
from pathlib import Path, PurePath
from os import DirEntry
from .repo import FSEntry


def stat_to_internal(info: DirEntry | Path) -> FSEntry:
    ans = FSEntry()
    ans['_is_file'] = info.is_file()
    from datetime import datetime, timezone

    def to_dt(x):
        # TODO: allow custom timezone
        return datetime.fromtimestamp(x, tz=timezone.utc)
    stat = info.stat()
    ans['mtime'] = to_dt(stat.st_mtime)
    ans['mtime_ns'] = stat.st_mtime_ns
    return ans


class SyncWorker:
    repo: Repository
    def __init__(self, repo) -> None:
        self.repo = repo
        pass

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
                    self.repo.set_file_entry(repo_path, stat_to_internal(entry))
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
