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

def main():
    from extractor import ArknightsExtractor
    worker = ArknightsExtractor()
    h = NamedHandler(worker.full_asset_list)
    register_handlers(h)
    worker.extract(h.callbacks)

if __name__=='__main__':
    main()
