from pathlib import Path
def get_crc32(path: Path, chunk_size=4096):
    value = 0
    with open(path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            from zlib import crc32
            value = crc32(data, value)
    return value

def main():
    file_list = []
    for p in Path('.').iterdir():
        if p.suffix == '.mkv':
            file_list.append(p)
        else:
            print(f'Unknown suffix: {p.name}')
    from tqdm import tqdm
    f: Path
    fails = False
    for f in tqdm(file_list):
        chksum = f'{get_crc32(f):08x}'
        if chksum not in f.name.lower():
            tqdm.write(f'Checksum {chksum} is invalid for {f.name}')
            fails = True
    if fails:
        exit(1)

if __name__ == '__main__':
    main()
