def resolve_deps(nodes, graph):
    stk = list(nodes)
    vis = set(stk)
    while len(stk) != 0:
        cur = stk.pop()
        if cur in vis: continue
        vis.add(cur)
        stk += graph[cur]
    return list(vis)

class ArknightsExtractor:
    def __init__(self) -> None:
        from ak_api import ArknightsApi
        self.api = ArknightsApi()
        from unity_utils import get_ab_containers
        with self.api.open_ab('torappu.ab') as f:
            c = get_ab_containers(f)
            assert len(c) == 1
            _, abm = list(c.items())[0]
            assert abm.type == 'AssetBundleManifest'
            abm = abm.read()
        id2path = dict(abm['AssetBundleNames'])
        self.dep_graph = {
            id2path[id]: [id2path[x] for x in info['AssetBundleDependencies']]
            for id, info in abm['AssetBundleInfos']
        }
        with self.api.open_ab('torappu_index.ab') as f:
            c = get_ab_containers(f)
            assert len(c) == 1
            base_path, idx = list(c.items())[0]
            assert idx.type == 'ResourceIndex'
            idx = idx.read()
        from urllib.parse import urljoin
        self.asset2bundle = {
            urljoin(base_path, a['assetName']): a['bundleName']
            for a in idx['assetToBundleList']
        }

    @property
    def full_asset_list(self):
        return list(self.asset2bundle.keys())

    def extract(self, handler):
        from collections import defaultdict
        bundle_queries = defaultdict(set)
        for a in handler:
            bundle_queries[self.asset2bundle[a]].add(a)
        from tqdm import tqdm
        pbar = tqdm(total=len(handler))
        for bundle_path, queries in bundle_queries.items():
            with self.api.create_env() as e:
                for temp_bundle in resolve_deps([bundle_path], self.dep_graph):
                    e.open_ab(temp_bundle)
                cur_bundle = e.open_ab(bundle_path)
                from pathlib import PurePath
                from unity_utils import get_ab_containers
                for name, obj in get_ab_containers(cur_bundle).items():
                    key_name = PurePath(name).with_suffix('').as_posix()
                    if key_name in queries:
                        handler[key_name](name, obj)
                        pbar.update()
        pbar.close()
