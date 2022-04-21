from .metadata import MetadataFilter

class HashlibFilter(MetadataFilter):
    def __init__(self, hash_type) -> None:
        self.hash_type = hash_type
        self.OPTION_NAME = 'save_' + hash_type
        self.METADATA_NAME = hash_type
        self.METADATA_TYPE = str

    def make_default_config(self, cfg):
        cfg[self.OPTION_NAME] = self.hash_type == 'sha256'

    def file_changed(self, cache, cur_stat):
        return False

    def put_index(self, cache, file_changed, cfg, output):
        if not cfg[self.OPTION_NAME]:
            return
        if file_changed:
            return False
        output[self.METADATA_NAME] = cache[self.METADATA_NAME]

    def parse_content(self, output):
        import hashlib
        ans = getattr(hashlib, self.hash_type)
        while chunk := (yield):
            ans.update(chunk)
        output[self.METADATA_NAME] = ans.hexdigest()

class CRC32Filter(HashlibFilter):
    def __init__(self) -> None:
        super().__init__('crc32')

    def parse_content(self, output):
        ans = 0
        while chunk := (yield):
            import zlib
            ans = zlib.crc32(chunk, ans)
        output[self.METADATA_NAME] = f'{ans:#010x}'
