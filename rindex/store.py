from abc import abstractmethod
from contextlib import contextmanager
import string
from typing import Generic, Hashable, TypeVar, Optional

K = TypeVar('K', bound=Hashable)
V = TypeVar('V')
valid_rand_char = string.ascii_uppercase + string.digits

def rand_str():
    from random import choices
    return ''.join(choices(valid_rand_char, k=8))

class CacheStore(Generic[K, V]):
    @abstractmethod
    def __getitem__(self, k: K) -> Optional[V]:
        r"""
        When None is returned, k is not present in the store
        """
        raise NotImplementedError

    @abstractmethod
    def __setitem__(self, k: K, v: V):
        raise NotImplementedError

    @abstractmethod
    def __delitem__(self, k: K):
        raise NotImplementedError

@contextmanager
def safe_dump(path, mode='wb'):
    from pathlib import Path
    path = Path(path)
    temp_path = path.with_suffix(f'.{rand_str()}.dat')
    with open(temp_path, mode=mode) as f:
        yield f
    temp_path.rename(path)
