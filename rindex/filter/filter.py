from typing import Generator, Optional
from ..entry import FileEntry, PathConfig
from pathlib import PurePath


class Filter:
    def load_path_config(self, opt: dict, output: PathConfig) -> None:
        r"""
        Load path config from options file
        Need to delete relavant option from opt
        or else they would be judged as unrecognized option
        """
        pass

    def calc_relative_config(self, cfg: PathConfig, rel_path: PurePath, output: PathConfig) -> None:
        pass

    def load_from_fscache(self, mtdt: dict, output: FileEntry) -> None:
        pass

    def load_from_index(self, mtdt: dict, output: FileEntry) -> None:
        pass

    def export_to_fscache(self, entry: FileEntry, output: FileEntry) -> None:
        r"""
        Need to be JSON-compatible
        """
        pass

    def export_to_index(self, entry: FileEntry, cfg: PathConfig, output: FileEntry) -> None:
        r"""
        Need to be TOML-compatible
        """
        pass

    def make_default_config(self, cfg: PathConfig) -> None:
        r"""
        This is the config for root
        """
        pass

    def file_changed(self, cache: FileEntry, cur_stat: FileEntry) -> bool:
        return False

    def put_index(self, cache: FileEntry, file_changed: bool, cfg: PathConfig, output: FileEntry) -> Optional[bool]:
        r"""
        return False if content is required
        """
        pass

    def parse_content(self, output: FileEntry) -> Generator[None, bytes, None]:
        pass
