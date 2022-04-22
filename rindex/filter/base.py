from abc import ABCMeta, abstractmethod
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

    def open_folder(self, repo: 'Filter', rel_path: PurePath, cfg: PathConfig) -> bool:
        r"""
        Return whether the folder is handled by this filter
        """
        return False
    
    def close_folder(self, repo: 'Filter', rel_path: PurePath, cfg: PathConfig) -> bool:
        r"""
        Return whether the folder is handled by this filter
        """
        return False


class MetadataFilter(Filter, metaclass=ABCMeta):
    OPTION_NAME: str
    METADATA_NAME: str
    METADATA_TYPE: type

    def load_path_config(self, opt, output):
        if self.OPTION_NAME in opt:
            val = opt.get(self.OPTION_NAME, False)
            assert isinstance(
                val, bool), f'Option {self.OPTION_NAME} should be a bool.'
            output[self.OPTION_NAME] = val
            del opt[self.OPTION_NAME]

    def calc_relative_config(self, cfg, rel_path, output):
        output[self.OPTION_NAME] = cfg[self.OPTION_NAME]

    def load_from_fscache(self, mtdt, output):
        if (v := mtdt.get(self.METADATA_NAME, None)) is not None:
            assert isinstance(
                v, self.METADATA_TYPE), f'Field {self.METADATA_NAME} has type {type(v)}, but {self.METADATA_TYPE} is expected.'
            output[self.METADATA_NAME] = v
            del mtdt[self.METADATA_NAME]

    def load_from_index(self, mtdt, output):
        if (v := mtdt.get(self.METADATA_NAME, None)) is not None:
            assert isinstance(
                v, self.METADATA_TYPE), f'Field {self.METADATA_NAME} has type {type(v)}, but {self.METADATA_TYPE} is expected.'
            output[self.METADATA_NAME] = v
            del mtdt[self.METADATA_NAME]

    def export_to_fscache(self, entry, output):
        if (v := entry.get(self.METADATA_NAME, None)) is not None:
            output[self.METADATA_NAME] = v

    def export_to_index(self, entry, cfg, output):
        if cfg[self.OPTION_NAME] and (v := entry.get(self.METADATA_NAME, None)) is not None:
            output[self.METADATA_NAME] = v

    @abstractmethod
    def make_default_config(self, cfg):
        raise NotImplementedError

    @abstractmethod
    def file_changed(self, cache, cur_stat):
        raise NotImplementedError

    @abstractmethod
    def put_index(self, cache, file_changed, cfg, output):
        raise NotImplementedError

    @abstractmethod
    def parse_content(self, output):
        raise NotImplementedError


class OptionFilter(Filter, metaclass=ABCMeta):
    @abstractmethod
    def load_path_config(self, opt: dict, output: PathConfig) -> None:
        pass

    @abstractmethod
    def calc_relative_config(self, cfg: PathConfig, rel_path: PurePath, output: PathConfig) -> None:
        pass

    @abstractmethod
    def make_default_config(self, cfg: PathConfig) -> None:
        pass
