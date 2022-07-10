def main():
    import sys
    assert len(sys.argv) >= 3
    from pathlib import Path
    from_dir = Path(sys.argv[1])
    to_dir = Path(sys.argv[2])
    files = []
    import os
    for f in to_dir.glob('**/*'):
        if not f.is_symlink():
            continue
        t = f.readlink()
        full_t = f.resolve(strict=False)
        f.unlink()
        if full_t.is_file():
            os.link(full_t, f)
        files.append((f, t, full_t))
    import subprocess as sp
    rsync_cmd = ['rsync']
    rsync_cmd += ['-rOHtP', '--delete']
    rsync_cmd += ['--modify-window', '1']
    rsync_cmd += ['--exclude', '.gitattributes']
    rsync_cmd += sys.argv[1:]
    sp.run(rsync_cmd)
    for f, t, full_t in files:
        if not f.is_file():
            continue
        if not full_t.is_file():
            continue
        s1, s2 = f.stat(), full_t.stat()
        if s1.st_dev == s2.st_dev and s1.st_ino == s2.st_ino:
            f.unlink()
            f.symlink_to(t)

if __name__=='__main__':
    main()
