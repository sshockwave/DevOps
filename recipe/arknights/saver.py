from pathlib import Path

def img_save_worker(queue):
    while True:
        target = queue.get()
        if target == 'exit':
            break
        else:
            path: Path
            img, path = target
            path.parent.mkdir(exist_ok=True, parents=True)
            if path.suffix == '.webp':
                img.save(path, lossless=True, quality=100, method=6)
            else:
                img.save(path)

class Saver:
    def __init__(self, save_path, num_threads=6) -> None:
        from queue import LifoQueue
        self.save_path = Path(save_path)
        self.num_workers = num_threads
        self.queue = LifoQueue(maxsize=self.num_workers * 2)
        from threading import Thread
        self.pool = [Thread(target=img_save_worker, args=(self.queue,)) for _ in range(self.num_workers)]
        for t in self.pool:
            t.start()

    def get_save_path(self, name):
        container_prefix = 'assets/torappu/dynamicassets/'
        if isinstance(name, Path):
            name = name.as_posix()
        assert name.startswith(container_prefix)
        name = name.removeprefix(container_prefix)
        return self.save_path / name

    def save_lossless(self, img, name):
        self.queue.put((img, self.get_save_path(name).with_suffix('.webp')))

    def close(self):
        for _ in self.pool:
            self.queue.put('exit')
        for t in self.pool:
            t.join()
