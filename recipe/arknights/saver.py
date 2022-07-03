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
            elif path.suffix == '.jxl':
                png_path = path.with_suffix('.png')
                import subprocess
                if path.exists():
                    ret = subprocess.run([
                        'djxl',
                        path.as_posix(),
                        png_path.as_posix(),
                    ], stderr=subprocess.DEVNULL)
                    assert ret.returncode == 0
                    from PIL import Image
                    exists = False
                    with Image.open(png_path) as img2:
                        from decoder import same_image
                        exists = same_image(img, img2)
                    png_path.unlink()
                    if exists:
                        continue
                img.save(png_path)
                ret = subprocess.run([
                    'cjxl',
                    png_path.as_posix(),
                    path.as_posix(),
                    '-q', '100',
                    '-e', '9',
                ], stderr=subprocess.DEVNULL)
                assert ret.returncode == 0
                png_path.unlink()
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
        self.updated_file_list = []

    def get_save_path(self, name):
        container_prefix = 'assets/torappu/dynamicassets/'
        if isinstance(name, Path):
            name = name.as_posix()
        assert name.startswith(container_prefix)
        name = name.removeprefix(container_prefix)
        self.updated_file_list.append(name)
        return self.save_path / name

    def save_lossless(self, img, name):
        self.queue.put((img, self.get_save_path(name).with_suffix('.jxl')))

    def open(self, name):
        return open(self.get_save_path(name))

    def close(self):
        for _ in self.pool:
            self.queue.put('exit')
        for t in self.pool:
            t.join()
