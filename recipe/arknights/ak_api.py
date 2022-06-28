from pathlib import Path
from contextlib import contextmanager

def get_api(url):
    import requests
    r = requests.get(url)
    assert r.ok
    return r.json()

def get_blob(url, save_loc: Path, progress_bar=True):
    import requests
    r = requests.get(url, stream=True)
    assert r.ok
    save_loc.parent.mkdir(parents=True, exist_ok=True)
    with open(save_loc, mode='wb') as f:
        if progress_bar:
            from tqdm import tqdm
            pbar = tqdm(
                total=int(r.headers.get('content-length')),
                desc=save_loc.name,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            )
        for chunk in r.iter_content(chunk_size=4096):
            f.write(chunk)
            if progress_bar:
                pbar.update(len(chunk))
        if progress_bar:
            pbar.close()

class ArknightsApi:
    network_config_endpoint = 'https://ak-conf.hypergryph.com/config/prod/official/network_config'
    def __init__(self, work_dir='assets'):
        self.assets = Path(work_dir)
        endpoints = self.get_network_locations()
        version = get_api(endpoints['hv'].format('Android'))['resVersion']
        self.asset_endpoint = endpoints['hu'] + '/Android/assets/' + version
        self.hot_update_list = self.get_hot_update_list(version)
        def list2dict(l):
            return {o['name']: o for o in l}
        self.hot_update_list['abInfos'] = list2dict(self.hot_update_list['abInfos'])
        self.hot_update_list['packInfos'] = list2dict(self.hot_update_list['packInfos'])

    def get_network_locations(self):
        import json
        content = json.loads(get_api(self.network_config_endpoint)['content'])
        assert content['configVer'] == '5'
        return content['configs'][content['funcVer']]['network']

    def get_hot_update_list(self, version):
        p = self.assets / 'hot_update_list.json'
        v = None
        import json
        if p.is_file():
            with open(p, mode='r') as f:
                v = json.load(f)
        if v is None or v['versionId'] != version:
            v = get_api(self.asset_endpoint + '/hot_update_list.json')
            from shutil import rmtree
            if self.assets.is_dir():
                rmtree(self.assets)
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, mode='w') as f:
                json.dump(v, f)
        return v

    def get_pack_path(self, name, refresh=False):
        from pathlib import PurePath
        fname = PurePath(name).with_suffix('.dat').as_posix().replace('/', '_')
        p = self.assets / fname
        if not p.is_file() or refresh:
            get_blob(self.asset_endpoint + '/' + fname, p)
        info = self.hot_update_list['packInfos'].get(name)
        if info is not None:
            assert p.stat().st_size == info['totalSize']
        return p

    class Environment:
        def __init__(self, api: 'ArknightsApi'):
            from unitypack.environment import UnityEnvironment
            self.api = api
            self.unity_env = UnityEnvironment()
            self.file_hndl = dict()
            self.bundle = dict()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, exc_traceback):
            self.close()

        def open_dat(self, name, refresh=False):
            if name in self.file_hndl: return self.file_hndl
            from zipfile import ZipFile
            self.file_hndl[name] = ZipFile(self.api.get_pack_path(name), 'r')
            return self.file_hndl[name]

        def open_ab(self, name: str, refresh=False):
            if name in self.bundle: return self.bundle[name]
            info = self.api.hot_update_list['abInfos'][name]
            z = self.open_dat(info.get('pid', name), refresh=refresh)
            assert z.getinfo(name).file_size == info['abSize']
            from unitypack import load
            self.bundle[name] = load(z.open(name, 'r'), self.unity_env)
            return self.bundle[name]

        def close(self):
            for v in self.file_hndl.values():
                v.close()

    def create_env(self):
        return self.Environment(self)

    @contextmanager
    def open_ab(self, name):
        with self.create_env() as e:
            yield e.open_ab(name)
