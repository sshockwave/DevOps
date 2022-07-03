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
    def __init__(self) -> None:
        from queue import LifoQueue
        self.num_workers = 6
        self.queue = LifoQueue(maxsize=self.num_workers * 2)
        from threading import Thread
        self.pool = [Thread(target=img_save_worker, args=(self.queue,)) for _ in range(self.num_workers)]
        for t in self.pool:
            t.start()

    def save_lossless(self, img, path):
        path = Path(path)
        self.queue.put((img, path.with_suffix('.webp')))

    def close(self):
        for _ in self.pool:
            self.queue.put('exit')
        for t in self.pool:
            t.join()
