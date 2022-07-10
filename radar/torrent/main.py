from pathlib import Path


def get_parser():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-r', '--repo', type=Path, nargs=1, help='Path to repo')
    parser.add_argument('-w', '--watch', action='store_true', help='Whether to add torrents from watch dir')
    parser.add_argument('-t', '--transmission', required=False, type=str, help='Transmission rpc url')
    parser.add_argument('-d', '--download-url', required=False, type=str, help='Where to download torrents')
    return parser

def size_repr(size):
    unit = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']
    for t in unit:
        if size < 1024:
            return f'{size:.2f}'.rstrip('0').rstrip('.') + t
        else:
            size /= 1024

class Tree:
    def __init__(self, name):
        self.name = name
        self.son = dict()
        self.size = 0

    def add_file(self, paths, size):
        x = self
        for v in paths:
            x.size += size
            nxt = x.son.get(v)
            if nxt is None:
                nxt = Tree(v)
                x.son[v] = nxt
            x = nxt
        x.size += size

    def gen_li(self, lines):
        assert len(self.son) == 0
        lines.append(f'<li>{self.name} <code title="{self.size}Bytes">{size_repr(self.size)}</code></li>')

    def gen_html(self, lines):
        assert len(self.son) > 0
        dirs = []
        files = []
        for s in self.son.values():
            if len(s.son) == 0:
                files.append(s)
            else:
                dirs.append(s)
        lines.append('<details>')
        lines.append(f'<summary>{self.name} <code>{size_repr(self.size)}</code></summary>')
        lines.append('<ul>')
        for d in dirs:
            lines.append('<li>')
            d.gen_html(lines)
            lines.append('</li>')
        for f in files:
            f.gen_li(lines)
        lines.append('</ul>')
        lines.append('</details>')

def mkwritable(path: Path):
    path.parent.mkdir(exist_ok=True, parents=True)

class TorrentRepo:
    def __init__(self, base_path: Path):
        self.path = base_path
        self.watch_dir = self.path / 'watch'

    @staticmethod
    def get_infohash(info):
        import hashlib
        from bencode import bencode
        return hashlib.sha1(bencode(info)).hexdigest()

    def add_raw_torrent(self, file_content, rel_path=Path('.')):
        from bencode import bdecode, bencode
        data = bdecode(file_content)
        infohash = self.get_infohash(data['info'])
        file_path = self.path / rel_path / infohash
        mkwritable(file_path)
        with open(file_path.with_suffix('.torrent'), 'wb') as f:
            f.write(bencode({'info': data['info']}))
        meta_path = file_path.with_suffix('.yml')
        meta = []
        if meta_path.exists():
            with open(meta_path, 'r') as f:
                import yaml
                from yaml import Loader
                meta += yaml.load(f, Loader=Loader)
        del data['info']
        if not any(t == data for t in meta):
            meta.append(data)
        mkwritable(meta_path)
        with open(meta_path, 'w') as f:
            import yaml
            yaml.dump(list(meta), f, allow_unicode=True)

    def scan_watch(self, watch_path=None):
        if watch_path is None:
            watch_path = self.watch_dir
        if not watch_path.exists():
            return
        import os
        for root, dirs, files in os.walk(watch_path):
            root = Path(root)
            for name in files:
                if name.endswith('.torrent'):
                    with open(root / name, 'rb') as f:
                        self.add_raw_torrent(f.read(), root.relative_to(watch_path))
                    (root / name).unlink()

    def gen_toc_html(self, torrent_path: Path, torrent_link: str):
        from bencode import bdecode
        with open(torrent_path, 'rb') as f:
            info = bdecode(f.read())['info']
        assert self.get_infohash(info) == torrent_path.stem
        root = Tree(f'<a href="{torrent_link}">{info["name"]}</a>')
        for it in info['files']:
            root.add_file(it['path'], it['length'])
        lines = []
        root.gen_html(lines)
        return '\n'.join(lines)

    def gen_dir_html(self, abs_path: Path):
        import os
        lines = []
        for root, dirs, files in os.walk(abs_path):
            root = Path(root)
            rel_path = root.relative_to(abs_path)
            first = True
            for name in sorted(files):
                if not name.endswith('.torrent'):
                    continue
                if first:
                    first = False
                    if root != abs_path:
                        lines.append(f'<h2>{rel_path.as_posix()}</h2>')
                lines.append(self.gen_toc_html(root / name, (rel_path / name).as_posix()))
        return '\n'.join(lines)

    def all_torrent_infohash(self):
        infohash = set()
        import os
        for root, dirs, files in os.walk(self.path):
            for name in files:
                if not name.endswith('.torrent'):
                    continue
                infohash.add(Path(name).stem)
        return list(infohash)

    def gen_all_torrent_html(self):
        lines = []
        def dfs1(path: Path):
            ret = dict()
            for t in path.iterdir():
                v = t
                if t.is_dir():
                    v = dfs1(t)
                elif t.suffix != '.torrent':
                    v = None
                if v is not None:
                    ret[t.name] = v
            if len(ret) > 0:
                return ret
        def dfs2(entries):
            if isinstance(entries, dict):
                for t, v in entries.items():
                    if isinstance(v, dict):
                        while isinstance(v, dict) and len(v) == 1:
                            for k, v2 in v.items():
                                pass
                            if not isinstance(v2, dict):
                                break
                            t += '/' + k
                            v = v2
                        lines.append(f'<li>{t}<ul>')
                        dfs2(v)
                        lines.append('</ul></li>')
                    else:
                        dfs2(v)
            else:
                path: Path = entries
                with open(path, 'rb') as f:
                    from bencode import bdecode
                    info = bdecode(f.read())['info']
                lines.append(f'<li><a href="{path.relative_to(self.path)}">{info["name"]}</a> <code>{path.stem}</code></li>')
        lines.append('<ul>')
        dfs2(dfs1(self.path))
        lines.append('</ul>')
        return '\n'.join(lines)

    def download_from_transmission(self, rpc_url, dl_url):
        from transmission_rpc import Client
        from urllib.parse import urlparse
        rpc_info = urlparse(rpc_url)
        from urllib.parse import unquote
        c = Client(
            protocol=rpc_info.scheme,
            username=rpc_info.username,
            password=unquote(rpc_info.password),
            host=rpc_info.hostname,
            port=rpc_info.port or 9091,
        )
        local = set(self.all_torrent_infohash())
        torrents = c.get_torrents()
        torrents = {t.hashString.lower(): t for t in torrents}
        remote = set(torrents)
        for infohash in remote.difference(local):
            import requests
            from urllib.parse import urljoin
            save_path = self.watch_dir / Path(torrents[infohash].download_dir).relative_to('/downloads') / f'{infohash}.torrent'
            mkwritable(save_path)
            with open(save_path, 'wb') as f:
                res = requests.get(urljoin(dl_url, f'{infohash}.torrent'))
                assert res.ok
                assert len(res.content) > 0
                f.write(res.content)
        unused = local.difference(remote)
        if len(unused) > 0:
            print('Torrents not present in remote:')
            for t in unused:
                print(t)

def main():
    args = get_parser().parse_args()
    repo = TorrentRepo(args.repo[0])
    if args.transmission is not None:
        assert args.download_url is not None
        repo.download_from_transmission(args.transmission, args.download_url)
    if args.watch:
        repo.scan_watch()
    repo.path.mkdir(exist_ok=True, parents=True)
    for p in repo.path.iterdir():
        if not p.is_dir():
            continue
        if p.name == '.git':
            continue
        with open(p / 'README.md', 'w') as f:
            f.write(repo.gen_dir_html(p))
    with open(repo.path / 'README.md', 'w') as f:
        f.write('# Torrents\n')
        f.write(repo.gen_all_torrent_html())

if __name__ == '__main__':
    main()
