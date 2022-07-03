use std::{path::{PathBuf, Path}, ffi::OsString, io, fs, collections};

pub struct LocalStorage {
    sym_pt: collections::HashSet<PathBuf>,
}

pub enum LocalStorageNode<'a> {
    File(FileNode),
    Dir(DirNode<'a>),
}

pub struct FileNode {
    path: PathBuf,
    metadata: fs::Metadata,
}

pub struct DirNode<'a> {
    path: PathBuf,
    store: &'a mut LocalStorage,
}

struct DirEntry<'a> {
    entry: fs::DirEntry,
    store: &'a mut LocalStorage,
}

struct DirIter<'a> {
    fs_iter: fs::ReadDir,
    store: &'a mut LocalStorage,
}

fn err_unknown_entry_type<P: AsRef<Path>>(path: P) -> io::Error {
    io::Error::new(
        std::io::ErrorKind::Unsupported,
        format!("Entry is neither a directory nor a file: '{:?}'", path.as_ref().as_os_str())
    )
}

fn err_symlink_loop<P: AsRef<Path>>(path: P) -> io::Error {
    io::Error::new(
        std::io::ErrorKind::Other,
        format!("Symlink loop detected at entry: '{:?}'", path.as_ref().as_os_str())
    )
}

impl LocalStorage {
    pub fn new() -> LocalStorage {
        LocalStorage { sym_pt: collections::HashSet::new() }
    }
    pub fn open<'a, P: AsRef<Path>>(&'a mut self, path: P) -> io::Result<LocalStorageNode<'a>> {
        let meta = fs::metadata(&path)?;
        if meta.is_file() {
            Ok(LocalStorageNode::File(FileNode {
                path: PathBuf::from(path.as_ref()),
                metadata: meta,
            }))
        } else if meta.is_dir() {
            Ok(LocalStorageNode::Dir(DirNode {
                path: PathBuf::from(path.as_ref()),
                store: self,
            }))
        } else {
            Err(err_unknown_entry_type(path))
        }
    }
}

impl<'a> DirIter<'a> {
    fn next(&'a mut self) -> Option<io::Result<DirEntry<'a>>> {
        match self.fs_iter.next() {
            Some(Ok(d)) => Some(Ok(DirEntry::<'a> {
                entry: d,
                store: self.store,
            })),
            Some(Err(e)) => Some(Err(e)),
            None => None,
        }
    }
}

impl<'a> DirEntry<'a> {
    fn name(&self) -> OsString {
        self.entry.file_name()
    }
    fn load(&'a mut self) -> io::Result<LocalStorageNode<'a>> {
        let ft = self.entry.file_type()?;
        let path = self.entry.path();
        // Don't use `self.store.open`
        // since it can reduce one invocation for dir
        if ft.is_file() {
            Ok(LocalStorageNode::File(FileNode {
                metadata: fs::metadata(&path)?,
                path: path,
            }))
        } else if ft.is_dir() {
            Ok(LocalStorageNode::Dir(DirNode {
                path: path,
                store: self.store,
            }))
        } else if ft.is_symlink() {
            let norm_path = fs::canonicalize(&path)?;
            let exists = self.store.sym_pt.insert(norm_path);
            if !exists {
                // Use original path to maximize readability
                self.store.open(path)
            } else {
                Err(err_symlink_loop(path))
            }
        } else {
            Err(err_unknown_entry_type(path))
        }
    }
}

impl<'a> FileNode {
    fn read(&'a mut self) -> io::Result<Box<dyn io::Read+'a>> {
        Ok(Box::new(fs::File::open(&self.path)?))
    }
}

impl<'a> DirNode<'a> {
    fn iter(&'a mut self) -> io::Result<DirIter<'a>> {
        Ok(DirIter {
            fs_iter: fs::read_dir(&self.path)?,
            store: self.store,
        })
    }
}
