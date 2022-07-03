use std::{path::{Path, PathBuf}, ffi::OsString, io, fs, collections::HashMap};

use toml_edit::{Document, de};
mod config;
use config::Config;

pub struct Repo {
}

const CONFIG_FILE_NAME: &str = "rmeta.toml";

impl Repo {
    fn from_options(options: HashMap<String, Config>) -> Repo {
        // TODO
    }
    fn from_document(doc: Document) -> Result<Repo, de::Error> {
        let options: HashMap<String, Config> = de::from_document(doc)?;
        Ok(Self::from_options(options))
    }
    fn from_config_path<P: AsRef<Path>>(path: P) -> io::Result<Repo> {
        Ok(Self::from_document(
            fs::read_to_string(path)?
            .parse::<Document>()
            .expect("Not a valid TOML file")
        ).expect("Not a valid config"))
    }
    fn open<P: AsRef<Path>>(path: P) -> io::Result<(Repo, Vec<OsString>)> {
        let repo_root = PathBuf::from(path.as_ref());
        let mut residual = Vec::new();
        loop {
            repo_root.push(CONFIG_FILE_NAME);
            if repo_root.exists() {
                let meta = repo_root.metadata()?;
                if meta.is_file() {
                    residual.reverse();
                    return Ok((Self::from_config_path(repo_root)?, residual))
                } else {
                    return Err(io::Error::new(
                        io::ErrorKind::Other,
                        format!("Found config at {:?} but not a file", repo_root.as_os_str()),
                    ))
                }
            }
            let pop1 = repo_root.pop();
            assert!(pop1);
            match repo_root.file_name() {
                Some(fname) => {
                    residual.push(OsString::from(fname));
                    repo_root.pop();
                },
                None => {
                    return Err(io::Error::new(
                        io::ErrorKind::Other,
                        format!("Config not found for '{:?}'", repo_root.as_os_str()),
                    ))
                }
            }
        }
    }
}
