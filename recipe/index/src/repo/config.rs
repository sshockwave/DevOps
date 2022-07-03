use serde::{self, Deserialize};
use toml_edit::{Document, de};

enum StorageType {
    
}

#[derive(Deserialize)]
struct PathConfig {
    standalone: Option<u32>,
}

struct ConfigTree {
}
