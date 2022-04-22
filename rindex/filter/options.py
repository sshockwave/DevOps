from abc import abstractmethod
from .filter import Filter, PathConfig, PurePath

class OptionFilter(Filter):
    @abstractmethod
    def load_path_config(self, opt: dict, output: PathConfig) -> None:
        pass

    @abstractmethod
    def calc_relative_config(self, cfg: PathConfig, rel_path: PurePath, output: PathConfig) -> None:
        pass
    
    @abstractmethod
    def make_default_config(self, cfg: PathConfig) -> None:
        pass

class StandaloneFilter(OptionFilter):
    OPTION_NAME = 'standalone'
    def load_path_config(self, opt: dict, output: PathConfig) -> None:
        if self.OPTION_NAME in opt:
            val = opt[self.OPTION_NAME]
            if isinstance(val, bool):
                val = 1
            assert isinstance(val, int)
            output[self.OPTION_NAME] = val

    def calc_relative_config(self, cfg: PathConfig, rel_path: PurePath, output: PathConfig) -> None:
        output[self.OPTION_NAME] = max(cfg[self.OPTION_NAME] - len(rel_path.parts), 0)

    def make_default_config(self, cfg: PathConfig) -> None:
        cfg[self.OPTION_NAME] = 1
