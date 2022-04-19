from typing import Callable, Iterable, Iterator, TypeVar, Generic, Tuple, Optional, Hashable
from pathlib import PurePath

T = TypeVar('T')
unit_path = PurePath('.')


class Tree(Generic[T]):
    def __init__(self) -> None:
        from collections import defaultdict
        self.sub = defaultdict(Tree[T])
        self.val: Optional[T] = None

    def __getitem__(self, path: PurePath) -> 'Tree[T]':
        x = self
        for s in path.parts:
            x = x.sub[s]
        return x

    def __delitem__(self, path: PurePath) -> None:
        trace = [(None, self)]
        x = self
        for s in path.parts:
            x = x.sub[s]
            trace.append((s, x))
        trace[-1].val = None
        while len(trace) >= 2:
            s, x = trace.pop()
            if x.val is None and len(x.sub) == 0:
                del trace[-1].sub[s]
            else:
                break

    def traverse_postorder(self) -> Iterator['Tree[T]']:
        for v in self.sub.values():
            yield from v.traverse_postorder()
        yield self

    def reduce(self, merge: Callable[[T, Iterator[T]], Optional[T]]) -> None:
        for x in self.traverse_postorder():
            x.val = merge(x.val, x.values())

    def copy(self) -> 'Tree[T]':
        that = Tree[T]()
        that.val = self.val
        for s, x in self.sub.items():
            that.sub[s] = x.copy()
        return that

    def last_value_node(self, path: PurePath) -> Tuple[PurePath, 'Tree[T]']:
        x = self
        result_path, result_x = [], self
        cur_path = []
        for s in path.parts:
            if s not in x.sub:
                break
            x = x.sub[s]
            cur_path.append(s)
            if x.val is not None:
                result_path += cur_path
                cur_path = []
                result_x = x
        return PurePath('/'.join(result_path)), result_x

    def chain_values(self, path: PurePath) -> Iterator[Optional[T]]:
        x = self
        yield x.val
        for s in path.parts:
            if x is not None:
                x = x.sub[s] if s in x.sub else None
            yield x and x.val

    def __iter__(self) -> Iterator[PurePath]:
        return self.keys()

    def keys(self) -> Iterator[PurePath]:
        return map(PurePath, self.sub.keys())

    def values(self) -> Iterator['Tree[T]']:
        return iter(self.sub.values())

    def items(self) -> Iterator[Tuple[PurePath, 'Tree[T]']]:
        return map(lambda x: (PurePath(x[0]), x[1]), self.sub.items())

    def safe_get(self, s: str) -> 'Tree[T]':
        return self.sub[s] if s in self.sub else tree_null


tree_null = Tree()


def top_sort(vertices: Iterable[Hashable], edges: Iterable[Tuple[Hashable, Hashable]]):
    dfn = list(vertices)
    n = len(dfn)
    idx = {v: i for i, v in enumerate(dfn)}
    deg = [0] * n
    nxt = [[] for _ in range(n)]
    for a, b in edges:
        a, b = idx[a], idx[b]
        nxt[a].append(b)
        deg[b] += 1
    ans = [i for i, d in enumerate(deg) if d == 0]
    p = 0
    while p < len(ans):
        x = ans[p]
        p += 1
        for t in nxt[x]:
            deg[t] -= 1
            if deg[t] == 0:
                ans.append(t)
    return [dfn[i] for i in ans]
