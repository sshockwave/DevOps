from pathlib import Path

class NamedHandler:
    def __init__(self, objs):
        self.universe = objs
        self.callbacks = dict()

    @property
    def items(self):
        return list(self.callbacks.keys())

    def register_filter(self, check, handler):
        for s in self.universe:
            if check(s):
                assert s not in self.callbacks
                self.callbacks[s] = handler

    def register_regex(self, pattern, handler):
        import re
        prog = re.compile(pattern)
        self.register_filter(lambda x: prog.search(x) is not None, handler)

    @property
    def not_handled(self):
        return set(self.universe).difference(set(self.callbacks.keys()))

def create_tree():
    from collections import defaultdict
    return defaultdict(create_tree)

def insert_tree(tree, name, val):
    names = name.split('/')
    cur = tree
    for t in names[:-1]:
        cur = cur[t]
    cur[names[-1]] = val

def register_handlers(h: NamedHandler):
    from handlers import handle_illust2
    h.register_regex('arts/(?:characters|npcs)/.*(?<!material)(?<!b)$', handle_illust2)
    from handlers import handle_poster
    h.register_regex('ui/kvimg/.*kv', handle_poster)
    h.register_regex('avg/backgrounds/', handle_poster)
    h.register_regex('avg/images/', handle_poster)
    h.register_regex('arts/ui/actarchivefileillustration/(?:(?!hub).)*$', handle_poster)
    from handlers import handle_avg_char
    h.register_regex('avg/characters/(?:(?!empty).)*$', handle_avg_char)
    from handlers import handle_text
    h.register_regex('/gamedata/story/', handle_text)
    # TODO

def need_update(repo_path: Path, api):
    hot_path = repo_path / 'hot_update_list.json'
    if not hot_path.exists():
        return True
    with open(hot_path, 'r') as f:
        import json
        data = json.load(f)
    ver_key = 'versionId'
    data2 = api.hot_update_list
    return data[ver_key] != data2[ver_key]

def main():
    from argparse import ArgumentParser
    parser = ArgumentParser(prog='arknights')
    parser.add_argument('-j', '--threads', type=int, default=6)
    parser.add_argument(
        '-o',
        '--output',
        type=Path,
        default='/mnt/c/Users/sshockwave/Downloads/output',
    )
    parser.add_argument('-n', '--dry-run', action='store_true')
    args = parser.parse_args()
    import handlers
    from saver import Saver
    handlers.saver = Saver(save_path=args.output, num_threads=args.threads)
    with handlers.saver:
        from ak_api import ArknightsApi
        from extractor import ArknightsExtractor
        api = ArknightsApi()
        if args.dry_run:
            if need_update(args.output, api):
                exit(0)
            else:
                exit(1)
        with open(args.output / 'hot_update_list.json', 'w') as f:
            import json
            json.dump(api.hot_update_list, f)
        worker = ArknightsExtractor(api)
        h = NamedHandler(worker.full_asset_list)
        register_handlers(h)
        worker.extract(h.callbacks)

if __name__=='__main__':
    main()
