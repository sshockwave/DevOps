from pathlib import Path
from pixivpy3 import AppPixivAPI

def to_jxl(path: Path):
    import subprocess
    ret = subprocess.run([
        'cjxl',
        path.as_posix(),
        path.with_suffix('.jxl').as_posix(),
        '-q', '100',
        '-e', '9',
    ], stderr=subprocess.DEVNULL)
    assert ret.returncode == 0

def get_url_filename(url):
    from urllib.parse import urlparse
    return Path(urlparse(url).path).name

class PixivRepo:
    def __init__(self, path, api: AppPixivAPI):
        self.base_path = Path(path)
        self.api = api
        self.post_list = []
        self.convert_list = []

    @staticmethod
    def extract_urls(data):
        page_count = data['page_count']
        url_list = []
        if page_count == 1:
            url_list.append(data['meta_single_page']['original_image_url'])
        else:
            assert page_count > 0
            url_list += (v['image_urls']['original'] for v in data['meta_pages'])
        return url_list

    def get_img_save_dir(self, data):
        return self.base_path / str(data['user']['id'])

    def get_json_save_path(self, data):
        return (self.get_img_save_dir(data) / str(data['id'])).with_suffix('.json')
    
    def download_img(self, data, url):
        save_path = self.get_img_save_dir(data) / get_url_filename(url)
        save_path.parent.mkdir(exist_ok=True, parents=True)
        with open(save_path, 'wb') as f:
            self.api.download(url, fname=f)
        if save_path.suffix != '.jxl':
            self.convert_list.append(save_path)

    def handle_post(self, data):
        img_type = data['type']
        assert img_type in ['illust', 'ugoira', 'manga']

        # Save images
        url_list = self.extract_urls(data)
        old_json = self.get_json_save_path(data)
        removed = False
        skip_download = False
        if url_list == ['https://s.pximg.net/common/images/limit_unknown_360.png']:
            removed = True
        if old_json.exists():
            with open(old_json, 'r') as f:
                import json
                old_data = json.load(f)
            old_url_list = self.extract_urls(old_data)
            if removed:
                data = old_data
                url_list = old_url_list
            if url_list == old_url_list:
                skip_download = True
            else:
                for url in old_url_list:
                    (self.get_img_save_dir(data) / get_url_filename(url)).with_suffix('.jxl').unlink()
        self.post_list.append(data)
        if skip_download:
            return
        for url in url_list:
            self.download_img(data, url)

    def remove_all_files_with_suffix(self, suf):
        import os
        for root, dirs, files in os.walk(self.base_path):
            for name in files:
                if name.endswith(suf):
                    os.remove(os.path.join(root, name))

    @staticmethod
    def gen_author_readme(info, posts):
        readme = []
        readme.append(f"<h1>{info['name']}</h1>")
        readme.append(f'<a href="https://www.pixiv.net/users/{info["id"]}">@{info["account"]}</a>\n')

        for p in posts:
            readme.append(f'<h3>{p["title"]}</h3>')
            for i, url in enumerate(PixivRepo.extract_urls(p)):
                fname = Path(get_url_filename(url)).with_suffix('.jxl').as_posix()
                readme.append(f'<a href="./{fname}">p{i}</a>')
            readme.append('<br>')
            for tag in p['tags']:
                tname = tag["name"]
                readme.append(f'<a href="https://www.pixiv.net/tags/{tname}">#{tname}</a>')
            readme.append('<br>')
            readme.append(p['caption'])
            readme.append('')
        return '\n'.join(readme)

    def gen_overall_readme(self, authors):
        from collections import defaultdict
        num_posts = defaultdict(int)
        tag_posts = defaultdict(list)
        for data in self.post_list:
            num_posts[data['user']['id']] += 1
            for tag in data['tags']:
                tag_posts[tag['name']].append(data)

        readme = list()
        readme.append('<h1>Pixiv Collection</h1>')

        readme.append('<h2>Authors</h2>')
        readme.append('<ul>')
        for author_id, info in authors.items():
            readme.append(f'<li><a href="./{author_id}/README.md">{info["name"]}</a> ({num_posts[author_id]} posts)</li>')
        readme.append('</ul>')
        return '\n'.join(readme)
        readme.append('<h2>Tags</h2>')
        for tname, posts in tag_posts.items():
            readme.append(f'<h3>{tname}</h3>')
            readme.append('<ul>')
            for data in posts:
                anchor = data['title'].lower().replace(' ', '-')
                user = data['user']
                readme.append(f'<li><a href="./{user["id"]}/README.md#{anchor}">{data["title"]}</a> - {user["name"]}</li>')
            readme.append('</ul>')
        return '\n'.join(readme)

    def remove_orphan(self):
        import os
        import re
        prog = re.compile('^(\d+)_p\d+.jxl$')
        for root, dirs, files in os.walk(self.base_path):
            for name in files:
                result = prog.match(name)
                if result:
                    pid = result.group(1)
                    json_file = (Path(root) / pid).with_suffix('.json')
                    if not json_file.exists():
                        (Path(root) / name).unlink()

    def post_process(self):
        self.remove_all_files_with_suffix('.json')
        self.remove_all_files_with_suffix('.md')
        for data in self.post_list:
            data.pop('total_view', None)
            data.pop('total_bookmarks', None)
            with open(self.get_json_save_path(data), 'w') as f:
                import json
                json.dump(data, f, indent=2)

        from collections import defaultdict
        author_info = dict()
        author_posts = defaultdict(list)
        for data in self.post_list:
            author_id = data['user']['id']
            if author_id in author_info:
                assert author_info[author_id] == data['user']
            else:
                author_info[author_id] = data['user']
            author_posts[author_id].append(data)
        for author_id, info in author_info.items():
            with open(self.base_path / str(author_id) / 'README.md', 'w') as f:
                f.write(self.gen_author_readme(info, author_posts[author_id]))

        with open(self.base_path / 'README.md', 'w') as f:
            f.write(self.gen_overall_readme(author_info))

def get_all_bookmark(api: AppPixivAPI, *args, **kwargs):
    max_bookmark_id = None
    while True:
        result = api.user_bookmarks_illust(*args, **kwargs, max_bookmark_id=max_bookmark_id)
        for data in result['illusts']:
            yield data
        from urllib.parse import urlparse
        next_url = result['next_url']
        if next_url is None:
            break
        qstring = urlparse(next_url).query
        for t in qstring.split('&'):
            k, v = t.split('=')
            if k == 'max_bookmark_id':
                max_bookmark_id = v

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('-u', '--uid', type=int, required=True)
    parser.add_argument('-o', '--output', type=Path, required=True)
    parser.add_argument('-t', '--token', type=str, required=True)
    import os
    parser.add_argument(
        '-j', '--threads',
        type=int,
        required=False,
        default=len(os.sched_getaffinity(0)),
    )
    args = parser.parse_args()
    api = AppPixivAPI()
    api.auth(refresh_token=args.token)
    repo = PixivRepo(args.output, api)
    from tqdm import tqdm
    for img in tqdm(get_all_bookmark(api, args.uid), desc='DL'):
        repo.handle_post(img)
    repo.post_process()
    from concurrent.futures import ThreadPoolExecutor
    num_threads = args.threads
    print(f'Running with {num_threads} threads')
    with ThreadPoolExecutor(num_threads) as exe:
        for _, img_path in tqdm(
            zip(exe.map(to_jxl, repo.convert_list), repo.convert_list),
            desc='JXL',
            total=len(repo.convert_list),
        ):
            img_path.unlink()
    repo.remove_orphan()

if __name__ == '__main__':
    main()
