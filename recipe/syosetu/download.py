from pathlib import Path
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm

ua = UserAgent()
headers = {
    'User-Agent': ua.chrome
}
proxies = {
   'http': 'http://192.168.208.1:7890',
   'https': 'http://192.168.208.1:7890',
}

def only(arr):
    assert len(arr) == 1
    return arr[0]

def filter_eol(it):
    return filter(lambda x: x != '\n', it)

def unwrap_text(soup):
    from bs4 import NavigableString
    assert isinstance(soup, NavigableString)
    return soup.get_text().strip()

def unwrap_innertext(soup):
    return unwrap_text(only(soup.contents))

def write_text(path: Path, text):
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, 'w') as f:
        f.write(text)

def migrate_children(a, b):
    for el in a.children:
        b.append(el.extract())

class SyosetuNovel:
    @staticmethod
    def req(url):
        return requests.get(url, headers=headers, proxies=proxies)

    def __init__(self, url) -> None:
        import re
        url_match = re.match(r'https://(?:\w*).syosetu.com/(\w*)/?', url)
        assert url_match
        self.id = url_match.group(1)
        self.url = url
        page = self.req(url).text
        page = BeautifulSoup(page, 'html.parser')
        self.intro = only(page.find_all(id='novel_ex')).decode_contents()
        self.title = unwrap_text(only(only(page.find_all('p', class_='novel_title')).contents))
        writer_div = only(page.find_all('div', class_='novel_writername'))
        writer_links = writer_div.find_all('a')
        if len(writer_links) != 0:
            author_el = only(writer_links)
            self.author = unwrap_text(only(author_el.contents))
            self.author_link = author_el.attrs['href']
        else:
            author_str = unwrap_innertext(writer_div)
            assert author_str.startswith('作者：')
            self.author = author_str[len('作者：'):]
            self.author_link = '#'
        toc_soup = only(page.find_all('div', class_='index_box'))
        self.toc = []
        chapter_cnt = 0
        for el in filter_eol(toc_soup.children):
            from bs4 import Tag
            assert isinstance(el, Tag)
            if el.name == 'div':
                assert el.attrs == {'class': ['chapter_title']}
                self.toc.append(unwrap_text(only(el.contents)))
                chapter_cnt += 1
            elif el.name == 'dl':
                assert el.attrs == {'class': ['novel_sublist2']}
                dd, dt = filter_eol(el.children)
                assert dd.attrs == {'class': ['subtitle']}
                assert dt.attrs == {'class': ['long_update']}
                href, = filter_eol(dd.children)
                url_match = re.match(f'^/{self.id}/(\d+)/$', href.attrs['href'])
                content_id = url_match.group(1)
                assert url_match
                from urllib.parse import urljoin
                info = {
                    'name': unwrap_text(only(href.contents)),
                    'id': content_id,
                    'url': urljoin(url, href.attrs['href']),
                    'path': f'./chapter{chapter_cnt:03}/{content_id}.md',
                }
                dt = list(filter_eol(dt.children))
                assert len(dt) in [1, 2]
                info['created_on'] = unwrap_text(dt[0])
                if len(dt) == 2:
                    assert dt[1].name == 'span'
                    info['updated_on'] = dt[1].attrs['title']
                    span_list = list(filter_eol(dt[1].children))
                    assert span_list[0] == '（'
                    assert span_list[1].name == 'u'
                    assert unwrap_text(only(span_list[1].contents)) == '改'
                    assert span_list[2] == '）'
                self.toc.append(info)

    def get_save_path(self):
        return f'./syosetu/{self.id}'

    def get_toc(self):
        return self.toc

    def gen_title_markdown(self):
        return f'* [{self.title}]({self.get_save_path()}) ({self.author})'

    def gen_readme(self):
        soup = BeautifulSoup()

        title = soup.new_tag('h1')
        title.string = self.title
        soup.append(title)

        soup.append(soup.new_string('作者：'))
        author = soup.new_tag('a', attrs={'href': self.author_link})
        author.string = self.author
        soup.append(author)

        details = soup.new_tag('details')
        summary = soup.new_tag('summary')
        summary.string = '紹介'
        details.append(summary)
        details.append(BeautifulSoup(self.intro, 'html.parser'))
        soup.append(details)

        dl = None
        for v in self.toc:
            if isinstance(v, str):
                if dl is not None:
                    soup.append(dl)
                dl = soup.new_tag('dl')
                title = soup.new_tag('h2')
                title.string = v
                soup.append(title)
            elif isinstance(v, dict):
                dt = soup.new_tag('dt')
                if dl is None:
                    dl = soup.new_tag('dl')
                dl.append(dt)
                href = soup.new_tag('a', attrs={'href': v['path']})
                dt.append(href)
                href.string = v['name']
                dd = soup.new_tag('dd')
                dl.append(dd)
                span1 = soup.new_tag('span')
                dd.append(span1)
                span1.string = v['created_on']
                if 'updated_on' in v:
                    span2 = soup.new_tag('span', attrs={'title': v['updated_on']})
                    span2.string = '（改）'
                    dd.append(span2)
            else:
                assert False
        if dl is not None:
            soup.append(dl)
        return soup.prettify()
    
    def gen_content(self, toc_item):
        page = self.req(toc_item['url']).text
        page = BeautifulSoup(page, 'html.parser')
        soup = BeautifulSoup()

        title = soup.new_tag('h1')
        soup.append(title)
        title.string = unwrap_innertext(only(page.find_all('p', class_='novel_subtitle')))
        assert title.string == toc_item['name']

        novel_p = page.find_all('div', id='novel_p')
        if len(novel_p) != 0:
            novel_p = only(novel_p)
            header = soup.new_tag('header')
            soup.append(header)
            soup.append(soup.new_tag('hr'))
            migrate_children(novel_p, header)

        honbun = only(page.find_all('div', id='novel_honbun'))
        content = soup.new_tag('section')
        soup.append(content)
        migrate_children(honbun, content)

        novel_a = page.find_all('div', id='novel_a')
        if len(novel_a) != 0:
            novel_a = only(novel_a)
            footer = soup.new_tag('footer')
            soup.append(soup.new_tag('hr'))
            soup.append(footer)
            migrate_children(novel_a, footer)

        return soup.prettify()

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('repo_dir', nargs=1, type=Path)
    args = parser.parse_args()
    repo_dir = args.repo_dir[0]
    print(f'Repo: {repo_dir}')
    with open(repo_dir / 'target_urls.txt', 'r') as f:
        target_urls = [l.strip() for l in f.readlines()]
    readme = '# Web Novels\n'
    for url in tqdm(target_urls):
        novel = SyosetuNovel(url)
        readme += novel.gen_title_markdown() + '\n'
        novel_path = repo_dir / novel.get_save_path()
        write_text(novel_path / 'README.md', novel.gen_readme())
        toc_path = novel_path / 'toc.json'
        if toc_path.exists():
            with open(toc_path, 'r') as f:
                import json
                old_toc = json.load(f)
        else:
            old_toc = []
        old_toc_map = {v['id']: v for v in old_toc if not isinstance(v, str)}
        new_toc = novel.get_toc()
        new_toc_map = {v['id']: v for v in new_toc if not isinstance(v, str)}
        for v in old_toc:
            if isinstance(v, str):
                continue
            if v['id'] not in new_toc_map:
                (novel_path / v['path']).unlink(missing_ok=True)
        for v in tqdm(new_toc, desc=novel.id):
            if isinstance(v, str):
                continue
            t = old_toc_map.get(v['id'])
            if t is None or t != v:
                if t is not None:
                    (novel_path / t['path']).unlink(missing_ok=True)
                write_text(novel_path / v['path'], novel.gen_content(v))
        with open(toc_path, 'w') as f:
            import json
            json.dump(new_toc, f, indent=2)
    with open(repo_dir / 'README.md', 'w') as f:
        f.write(readme)

if __name__ == '__main__':
    main()
