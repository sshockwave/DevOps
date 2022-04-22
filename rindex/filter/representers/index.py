from ..base import Filter
from pathlib import PurePath
from ...entry import DirEntry, PathConfig


def is_empty(path):
    from os import scandir
    with scandir(path) as it:
        return not any(it)


OPTION_DATA_NAME = 'data'

def get_opt_data(opt: dict, key: str):
    if OPTION_DATA_NAME not in opt:
        return
    data = opt[OPTION_DATA_NAME]
    assert isinstance(data, dict), "Option 'data' should be a dict."
    assert len(data) == 1, 'At most one choice in `data` can be specified.'
    if key not in opt:
        return
    val = data[key]
    del opt[OPTION_DATA_NAME]
    return val


class IndexRepresenter(Filter):
    OPTION_NAME = 'index'
    def load_path_config(self, opt: dict, output) -> None:
        v = get_opt_data(opt, self.OPTION_NAME)
        if v is None:
            return
        output[OPTION_DATA_NAME] = {self.OPTION_NAME: True}

    def make_default_config(self, cfg) -> None:
        cfg[OPTION_DATA_NAME] = {self.OPTION_NAME: True}

    def open_folder(self, repo: Filter, rel_path: PurePath, cfg: PathConfig) -> bool:
        if self.OPTION_NAME not in cfg[OPTION_DATA_NAME]:
            return False
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

    def close_folder(self, repo: Filter, rel_path: PurePath, cfg: PathConfig) -> bool:
        if self.OPTION_NAME not in cfg[OPTION_DATA_NAME]:
            return False
        val: DirEntry = repo.dir_cache[rel_path]
        val['_ref_count'] -= 1
        if val['_ref_count'] > 0:
            repo.dir_cache[rel_path] = val
            return
        if '_exported' not in val:
            repo.export_folder_index(rel_path, allow_unused=True)
        abs_path = repo.repo_root / rel_path
        if '_exported' not in repo.dir_cache[rel_path]:
            (abs_path / repo.INDEX_FILENAME).unlink(missing_ok=True)
        if abs_path.exists() and abs_path.is_dir() and is_empty(abs_path):
            abs_path.rmdir()
        del repo.dir_cache[rel_path]
        if rel_path.parent != rel_path:
            repo.close_folder(rel_path.parent)
        return True
