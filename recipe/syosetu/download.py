import re
from copy import copy
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import List
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import requests
from tqdm import tqdm
from urllib.parse import urljoin

ua = UserAgent()
headers = {
    'User-Agent': ua.chrome
}
proxies = {
   #'http': 'http://192.168.208.1:7890',
   #'https': 'http://192.168.208.1:7890',
}

def only(arr):
    el = None
    for a in arr:
        assert el is None
        el = a
        break
    assert el is not None
    return el

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
        from copy import copy
        b.append(copy(el))

def get_child(soup):
    return only(filter_eol(soup.children))

def find_uniq(soup, *args, **kwargs):
    return only(soup.find_all(*args, **kwargs))

def write_html(path, src):
    from tidylib import tidy_fragment
    document, errors = tidy_fragment(str(src))
    assert not errors
    write_text(path, document)

class BaseNovel(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def match(url):
        pass

    @abstractmethod
    def get_save_path(self):
        pass

    @abstractmethod
    def get_toc(self):
        pass

    def gen_title_markdown(self):
        return f'【{self.author}】[{self.title}]({self.get_save_path()}/README.md)'

    @abstractmethod
    def gen_readme(self):
        pass

    @abstractmethod
    def gen_content(self, toc_item):
        pass

class SyosetuNovel(BaseNovel):
    @staticmethod
    def req(url):
        return requests.get(url, headers=headers, proxies=proxies, cookies={'over18': 'yes'})

    url_prog = re.compile(r'^https://(?:\w*).syosetu.com/(\w*)/?$')
    @classmethod
    def match(cls, url):
        return cls.url_prog.match(url)

    def __init__(self, url) -> None:
        url_match = self.match(url)
        self.id = url_match.group(1)
        self.url = url
        page = self.req(url).text
        page = BeautifulSoup(page, 'html.parser')
        self.intro = find_uniq(page, id='novel_ex').decode_contents()
        self.title = unwrap_innertext(find_uniq(page, 'p', class_='novel_title'))
        writer_div = find_uniq(page, 'div', class_='novel_writername')
        writer_links = writer_div.find_all('a')
        if len(writer_links) != 0:
            author_el = only(writer_links)
            self.author = unwrap_innertext(author_el)
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
                self.toc.append({
                    'no_store': True,
                    'name': unwrap_innertext(el)
                })
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
                info = {
                    'name': unwrap_innertext(href),
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
                    assert unwrap_innertext(span_list[1]) == '改'
                    assert span_list[2] == '）'
                self.toc.append(info)

    def get_save_path(self):
        return f'./syosetu/{self.id}'

    def get_toc(self):
        return self.toc

    def gen_readme(self):
        soup = BeautifulSoup()

        title = soup.new_tag('h1')
        title.string = self.title
        soup.append(title)

        soup.append(soup.new_string('【作者】'))
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
            if v.get('no_store'):
                if dl is not None:
                    soup.append(dl)
                dl = soup.new_tag('dl')
                title = soup.new_tag('h2')
                title.string = v['name']
                soup.append(title)
            else:
                dt = soup.new_tag('dt')
                if dl is None:
                    dl = soup.new_tag('dl')
                dl.append(dt)
                href = soup.new_tag('a', attrs={'href': v['path']})
                dt.append(href)
                href.string = v['name']
                dd = soup.new_tag('dd')
                dl.append(dd)
                dd.append(soup.new_string(v['created_on']))
                if 'updated_on' in v:
                    dd.append(soup.new_string(f'（{v["updated_on"]}）'))
        if dl is not None:
            soup.append(dl)
        return str(soup)

    def gen_content(self, toc_item):
        page = self.req(toc_item['url']).text
        page = BeautifulSoup(page, 'html.parser')
        soup = BeautifulSoup()

        title = soup.new_tag('h1')
        soup.append(title)
        title.string = unwrap_innertext(find_uniq(page, 'p', class_='novel_subtitle'))
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

        return str(soup)

class KakuyomuNovel(BaseNovel):
    @staticmethod
    def req(url):
        return requests.get(url)

    url_prog = re.compile(r'^https://kakuyomu.jp/works/(\d*)$')
    @classmethod
    def match(cls, url):
        return cls.url_prog.match(url)

    def __init__(self, url) -> None:
        url_match = self.match(url)
        self.id = url_match.group(1)
        self.url = url
        page = self.req(url).text
        page = BeautifulSoup(page, 'html.parser')

        title_href = get_child(find_uniq(page, id='workTitle'))
        assert title_href.attrs['href'] == f'/works/{self.id}'
        self.title = unwrap_innertext(title_href)

        author_href = get_child(find_uniq(page, id='workAuthor-activityName'))
        self.author = unwrap_innertext(author_href)
        self.author_link = urljoin(url, author_href.attrs['href'])

        genre_href = get_child(find_uniq(page, id='workGenre'))
        self.genre = unwrap_innertext(genre_href)
        self.genre_link = urljoin(url, genre_href.attrs['href'])

        self.atten_list = []
        atten_el = page.find_all(id='workMeta-attention')
        if atten_el:
            for li in only(atten_el).children:
                assert li.name == 'li'
                assert li.attrs == {}
                self.atten_list.append(unwrap_innertext(li))

        self.tag_list = []
        tag_el = page.find_all(id='workMeta-tags')
        if tag_el:
            for li in only(tag_el).children:
                assert li.name == 'li'
                assert li.attrs == {'itemprop': 'keywords'}
                li = get_child(li)
                self.tag_list.append({
                    "url": urljoin(url, li.attrs['href']),
                    "name": unwrap_innertext(li),
                })

        self.catchphrase_style = find_uniq(page, id='catchphrase').attrs['style']
        self.catchpharse = unwrap_innertext(find_uniq(page, id='catchphrase-body'))
        assert self.author == unwrap_innertext(find_uniq(page, id='catchphrase-authorLabel'))

        self.intro = copy(find_uniq(page, id='introduction'))
        show_more = self.intro.find_all(class_='ui-truncateTextButton-restText')
        if show_more:
            show_more = only(show_more).extract()
            find_uniq(self.intro, class_='ui-truncateTextButton-expandButton').extract()
            migrate_children(show_more, self.intro)

        self.toc = []
        chapter_cnt = 0
        for el in find_uniq(page, 'ol', class_='widget-toc-items'):
            if el == '\n':
                continue
            from bs4 import Tag
            assert isinstance(el, Tag)
            assert el.name == 'li'
            if 'widget-toc-chapter' in el.attrs['class']:
                assert 'widget-toc-level1' in el.attrs['class']
                el = get_child(el)
                assert el.name == 'span'
                self.toc.append({
                    'no_store': True,
                    'name': unwrap_innertext(el),
                })
            elif 'widget-toc-episode' in el.attrs['class']:
                el = get_child(el)
                assert el.attrs['class'] == ['widget-toc-episode-episodeTitle']
                title_el, time_el = filter_eol(el.children)
                assert title_el.name == 'span'
                assert time_el.name == 'time'
                assert 'widget-toc-episode-titleLabel' in title_el.attrs['class']
                assert time_el.attrs['class'] == ['widget-toc-episode-datePublished']
                url_match = re.match(f'^/works/{self.id}/episodes/(\d+)$', el.attrs['href'])
                assert url_match
                content_id = url_match.group(1)
                self.toc.append({
                    'name': unwrap_innertext(title_el),
                    'id': content_id,
                    'url': urljoin(url, el.attrs['href']),
                    'updated_on': time_el.attrs['datetime'],
                    'updated_str': unwrap_innertext(time_el),
                    'path': f'./chapter{chapter_cnt:03}/{content_id}.md',
                })
            else:
                assert False

    def get_save_path(self):
        return f'./kakuyomu/{self.id}'

    def get_toc(self):
        return self.toc

    def gen_readme(self):
        soup = BeautifulSoup()

        soup.append(title := soup.new_tag('h1'))
        title.string = self.title

        soup.append(blockq := soup.new_tag('blockquote'))
        blockq.string = self.catchpharse
        blockq.attrs['style'] = self.catchphrase_style

        soup.append('【　作者　】')
        author = soup.new_tag('a', attrs={'href': self.author_link})
        author.string = self.author
        soup.append(author)
        soup.append(soup.new_tag('br'))

        soup.append('【ジャンル】')
        genre = soup.new_tag('a', attrs={'href': self.genre_link})
        genre.string = self.genre
        soup.append(genre)
        soup.append(soup.new_tag('br'))

        if self.atten_list:
            soup.append('【注意事項】' + ' / '.join(self.atten_list))
            soup.append(soup.new_tag('br'))

        if self.tag_list:
            first = True
            soup.append('【　タグ　】')
            for t in self.tag_list:
                if first:
                    first = False
                else:
                    soup.append(' / ')
                tag_href = soup.new_tag('a', attrs={'href': t['url']})
                soup.append(tag_href)
                tag_href.string = t['name']
            soup.append(soup.new_tag('br'))

        soup.append(details := soup.new_tag('details'))
        details.append(summary := soup.new_tag('summary'))
        summary.string = '紹介'
        migrate_children(self.intro, details)

        dl = None
        for v in self.toc:
            if v.get('no_store'):
                if dl is not None:
                    soup.append(dl)
                dl = soup.new_tag('dl')
                title = soup.new_tag('h2')
                title.string = v['name']
                soup.append(title)
            else:
                dt = soup.new_tag('dt')
                if dl is None:
                    dl = soup.new_tag('dl')
                dl.append(dt)
                href = soup.new_tag('a', attrs={'href': v['path']})
                dt.append(href)
                href.string = v['name']
                dl.append(dd := soup.new_tag('dd'))
                updated_time = soup.new_tag('span', attrs={'title': v['updated_on']})
                updated_time.string = v['updated_str']
                dd.append(updated_time)
        if dl is not None:
            soup.append(dl)

        return str(soup)

    def gen_content(self, toc_item):
        page = self.req(toc_item['url']).text
        page = BeautifulSoup(page, 'html.parser')
        soup = BeautifulSoup()

        soup.append(title := soup.new_tag('h1'))
        soup.append('\n')
        title.string = unwrap_innertext(find_uniq(page, 'p', class_='widget-episodeTitle'))

        content_el = find_uniq(page, 'div', class_='widget-episodeBody')
        migrate_children(content_el, soup)

        return str(soup)

novel_types: List[BaseNovel] = [
    SyosetuNovel,
    KakuyomuNovel
]

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('repo_dir', nargs=1, type=Path)
    args = parser.parse_args()
    repo_dir = args.repo_dir[0]
    print(f'Repo: {repo_dir}')
    with open(repo_dir / 'source.md', 'r') as f:
        readme = BeautifulSoup(f, 'html.parser')
    for anchor in tqdm(readme.find_all('a', class_='download')):
        url = unwrap_innertext(anchor)
        NovelClass = only([c for c in novel_types if c.match(url)])
        novel = NovelClass(url)
        anchor.replace_with(novel.gen_title_markdown())
        novel_path = repo_dir / novel.get_save_path()
        write_html(novel_path / 'README.md', novel.gen_readme())
        toc_path = novel_path / 'toc.json'
        if toc_path.exists():
            with open(toc_path, 'r') as f:
                import json
                old_toc = json.load(f)
        else:
            old_toc = []
        old_toc_map = {v['id']: v for v in old_toc if isinstance(v, dict) and not v.get('no_store')}
        new_toc = novel.get_toc()
        new_toc_map = {v['id']: v for v in new_toc if not v.get('no_store')}
        for v in old_toc:
            if not isinstance(v, dict) or v.get('no_store'):
                continue
            if v['id'] not in new_toc_map:
                (novel_path / v['path']).unlink(missing_ok=True)
        for v in tqdm(new_toc, desc=novel.get_save_path()):
            if v.get('no_store'):
                continue
            t = old_toc_map.get(v['id'])
            if t is None or t != v:
                if t is not None:
                    (novel_path / t['path']).unlink(missing_ok=True)
                write_html(novel_path / v['path'], novel.gen_content(v))
        with open(toc_path, 'w') as f:
            import json
            json.dump(new_toc, f, indent=2)
    write_text(repo_dir / 'README.md', str(readme))

if __name__ == '__main__':
    main()
