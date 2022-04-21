from abc import ABCMeta, abstractmethod
from typing import Generator, Optional
from ..entry import FileEntry, PathConfig
from pathlib import PurePath


class Filter(metaclass=ABCMeta):
    @abstractmethod
    def load_path_config(self, opt: dict, output: PathConfig) -> None:
        r"""
        Load path config from options file
        Need to delete relavant option from opt
        or else they would be judged as unrecognized option
        """
        raise NotImplementedError

    @abstractmethod
    def calc_relative_config(self, cfg: PathConfig, rel_path: PurePath, output: PathConfig) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_from_fscache(self, mtdt: dict, output: FileEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    def load_from_index(self, mtdt: dict, output: FileEntry) -> None:
        raise NotImplementedError

    @abstractmethod
    def export_to_fscache(self, entry: FileEntry, output: FileEntry) -> None:
        r"""
        Need to be JSON-compatible
        """
        raise NotImplementedError

    @abstractmethod
    def export_to_index(self, entry: FileEntry, cfg: PathConfig, output: FileEntry) -> None:
        r"""
        Need to be TOML-compatible
        """
        raise NotImplementedError

    @abstractmethod
    def make_default_config(self, cfg: PathConfig) -> None:
        raise NotImplementedError

    @abstractmethod
    def file_changed(self, cache: FileEntry, cur_stat: FileEntry) -> bool:
        raise NotImplementedError

    @abstractmethod
    def put_index(self, cache: FileEntry, file_changed: bool, cfg: PathConfig, output: FileEntry) -> Optional[bool]:
        r"""
        return False if content is required
        """
        raise NotImplementedError

    @abstractmethod
    def parse_content(self, output: FileEntry) -> Generator[None, bytes, None]:
        raise NotImplementedError
