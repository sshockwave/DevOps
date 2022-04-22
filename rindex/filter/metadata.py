from .base import MetadataFilter
from datetime import datetime

class ModtimeFilter(MetadataFilter):
    OPTION_NAME = 'save_mtime'
    METADATA_NAME = 'mtime'
    TIMEZONE_NAME = 'timezone'
    METADATA_TYPE = datetime

    def load_path_config(self, opt, output):
        val = opt.get(self.OPTION_NAME, False)
        assert isinstance(val, bool), f'Option {self.OPTION_NAME} should be a bool.'
        output[self.OPTION_NAME] = val
        if self.OPTION_NAME in opt:
            del opt[self.OPTION_NAME]
        if self.TIMEZONE_NAME in opt:
            val = opt[self.TIMEZONE_NAME]
            del opt[self.TIMEZONE_NAME]
            assert isinstance(val, str), f'Option {self.TIMEZONE_NAME} should be a str.'
            import pytz
            output[self.TIMEZONE_NAME] = pytz.timezone(val)

    def load_from_fscache(self, mtdt, output):
        if (v := mtdt.get(self.METADATA_NAME, None)) is not None:
            assert isinstance(v, str)
            output[self.METADATA_NAME] = datetime.fromisoformat(v)

    def export_to_fscache(self, entry, output):
        if (v := entry.get(self.METADATA_NAME)):
            assert isinstance(v, datetime)
            output[self.METADATA_NAME] = v.isoformat()

    def export_to_index(self, entry, cfg, output):
        if cfg[self.OPTION_NAME] and (v := entry.get(self.METADATA_NAME)):
            output[self.METADATA_NAME] = v.astimezone(cfg[self.TIMEZONE_NAME])

    def make_default_config(self, cfg):
        cfg[self.OPTION_NAME] = True
        from datetime import datetime
        cfg[self.TIMEZONE_NAME] = datetime.fromtimestamp(0).astimezone().tzinfo

    def file_changed(self, cache, cur_stat):
        return cache.get(self.METADATA_NAME) != cur_stat[self.METADATA_NAME]

    def put_index(self, cache, file_changed, cfg, output):
        # Should have been fetched before checking file_changed()
        assert self.METADATA_NAME in output

    def parse_content(self, output):
        assert False

class ModtimeNSFilter(MetadataFilter):
    OPTION_NAME = 'save_mtime_ns'
    METADATA_NAME = 'mtime_ns'
    METADATA_TYPE = int

    def make_default_config(self, cfg):
        cfg[self.OPTION_NAME] = False

    def file_changed(self, cache, cur_stat):
        return False

    def put_index(self, cache, file_changed, cfg, output):
        # Should have been fetched before checking file_changed()
        assert self.METADATA_NAME in output

    def parse_content(self, output):
        assert False

class SizeFilter(MetadataFilter):
    OPTION_NAME = 'save_size'
    METADATA_NAME = 'size'
    METADATA_TYPE = int

    def make_default_config(self, cfg):
        cfg[self.OPTION_NAME] = True

    def file_changed(self, cache, cur_stat):
        return cache.get(self.METADATA_NAME) != cur_stat[self.METADATA_NAME]

    def put_index(self, cache, file_changed, cfg, output):
        # Should have been fetched before checking file_changed()
        assert self.METADATA_NAME in output

    def parse_content(self, output):
        assert False
