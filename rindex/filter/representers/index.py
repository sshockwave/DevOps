from ..base import Filter
from pathlib import PurePath
from ...entry import DirEntry

class IndexRepresenter(Filter):
    def open_folder(self, repo: Filter, rel_path: PurePath) -> bool:
        val: DirEntry = repo.dir_cache.get(rel_path)
        if val is not None:
            val['_ref_count'] += 1
            repo.dir_cache[rel_path] = val
            return
        if rel_path.parent != rel_path:
            repo.open_folder(rel_path.parent)
        # Check if index file exists
        index_file = repo.repo_root / rel_path / repo.INDEX_FILENAME
        if index_file.exists():
            # A full scan is needed,
            # otherwise data loss can happen on config change.
            repo.load_index(index_file)
        val = DirEntry()
        val['_ref_count'] = 1
        repo.dir_cache[rel_path] = val
        return True
