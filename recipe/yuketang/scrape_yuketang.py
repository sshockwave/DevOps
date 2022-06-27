import requests
from pathlib import Path
from pathlib import PurePath

def read_json(file: Path):
    with open(file, 'r') as f:
        import json
        return json.load(f)

def get_m3u8():
    return read_json('./replay.json')['data']['live']

def fetch_video(cfg, oput: Path):
    url = cfg['url']
    oput.mkdir(exist_ok=True, parents=True)
    from urllib.parse import urlparse, urljoin, urlunparse
    from tqdm import tqdm
    with open(oput / 'filelist.txt', 'w') as filelist:
        for a in tqdm(requests.get(url).text.split('\n')):
            if a=='': continue
            if a.startswith('#'): continue
            cur = urljoin(url, a)
            cur = urlparse(cur)
            cur = cur._replace(query='&'.join(filter(lambda x: not x.startswith('resolution='), cur.query.split('&'))))
            fname = PurePath(cur.path).name
            print(fname, file=filelist)
            filelist.flush()
            with open(oput / fname, 'wb') as f:
                f.write(requests.get(urlunparse(cur)).content)

def main():
    for i, t in enumerate(get_m3u8()):
        fetch_video(t, Path(f'./oput{i}'))

if __name__ == '__main__':
    main()
