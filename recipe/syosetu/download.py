from pathlib import Path
from playwright.sync_api import sync_playwright, Page
from bs4 import BeautifulSoup

proxies = {
   'http': 'http://192.168.208.1:7890',
}

def only(arr):
    assert len(arr) == 1
    return arr[0]

def filter_eol(it):
    return filter(lambda x: x != '\n', it)

def unwrap_text(soup):
    from bs4 import NavigableString
    assert isinstance(soup, NavigableString)
    return soup.get_text()

def write_text(path: Path, text):
    path.parent.mkdir(exist_ok=True, parents=True)
    with open(path, 'w') as f:
        f.write(text)

class SyosetuNovel:
    def __init__(self, url, page: Page) -> None:
        import re
        url_match = re.match(r'https://ncode.syosetu.com/(\w*)/?', url)
        assert url_match
        self.id = url_match.group(1)
        self.page = page
        page.goto(url)


        t = page.locator('a.more')
        if t.count() > 0:
            t.click()
        self.intro = page.locator('#novel_ex').inner_html()

        self.title = page.locator('p.novel_title').inner_text()
        author_el = page.locator('div.novel_writername a')
        self.author = author_el.inner_text()
        self.author_link = author_el.get_attribute('href')
        toc_soup = BeautifulSoup(page.locator('div.index_box').inner_html(), 'html.parser')
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
                assert url_match
                info = {
                    'name': unwrap_text(only(href.contents)),
                    'path': f'./chapter{chapter_cnt:03}/{url_match.group(1)}',
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

    def gen_title_markdown(self):
        return f'* [{self.title}]({self.get_save_path()}) - [{self.author}]({self.author_link})'

    def gen_readme_markdown(self):
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

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('repo_dir', nargs=1, type=Path)
    args = parser.parse_args()
    repo_dir = args.repo_dir[0]
    print(f'Repo: {repo_dir}')
    with open(repo_dir / 'target_urls.txt', 'r') as f:
        target_urls = {l.strip() for l in f.readlines()}
    with sync_playwright() as p:
        browser = p.chromium.launch(proxy={
            "server": proxies['http'],
        })
        readme = '# Web Novels\n'
        page = browser.new_page()
        for url in target_urls:
            novel = SyosetuNovel(url, page)
            readme += novel.gen_title_markdown() + '\n'
            write_text(repo_dir / novel.get_save_path() / 'README.md', novel.gen_readme_markdown())
        page.close()
        browser.close()
        with open(repo_dir / 'README.md', 'w') as f:
            f.write(readme)

if __name__ == '__main__':
    main()
