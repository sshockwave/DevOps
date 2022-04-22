from .base import Filter
from typing import List


def make_filters() -> List[Filter]:
    from .metadata import ModtimeFilter, ModtimeNSFilter, SizeFilter
    from .checksum import HashlibFilter, CRC32Filter
    from .options import StandaloneFilter
    return [
        SizeFilter(),
        ModtimeFilter(),
        ModtimeNSFilter(),
        StandaloneFilter(),
        CRC32Filter(),
        HashlibFilter('md5'),
        HashlibFilter('sha1'),
        HashlibFilter('sha256'),
        HashlibFilter('sha512'),
    ]
