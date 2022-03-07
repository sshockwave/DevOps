# DevOps

## Platforms
### Rootless Linux
The rootless mode is recommended for most scenarios since it can be used on shared servers and does no harm to the system.
Scripts are built around [conda](https://conda.io) because it:
* is a rootless package manager that neatly installs and removes binaries;
* comes with all the dependencies and thus works on most linux distributions;
* uses environments to separate different installations of packages;
* supports installing self-compiled binaries;
* is actively maintained by the data science community.

To start using conda, the installation file has to be downloaded to the host.
See the [doc](https://docs.conda.io/en/latest/miniconda.html) for more information.

```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
# Or use curl
# curl https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh > miniconda.sh

# Alternative downloads:

PREFIX="${HOME}/miniconda3"
sh miniconda.sh -b -p "${PREFIX}" # Install in silent mode
source ${PREFIX}/bin/activate # Activate conda in the current shell
conda init # Modify the bash init scripts to activate conda on startup
```

Useful mirrors:
* https://mirror.tuna.tsinghua.edu.cn/help/anaconda/

Using proxies by adding the following lines to `~/.condarc`:
```yaml
proxy_servers:
    http: http://user:pass@corp.com:8080
    https: https://user:pass@corp.com:8080
```

Conda uses the idea of environments, each of which is contained in a single folder.
Many commands can be paired with `-n <env_name>` or `-p <prefix>`
to specify the exact environment to operate on.
```bash
conda create -n myenv # Create an environment
conda activate myenv # Enter the environment
conda install python=3.10 -c <channel> # Install packages
conda remove python # Remove packages
conda deactivate # Exit the environment
conda info --envs # List all envs
conda remove -n myenv --all # Remove the environment
conda env export --from-history # Export marked packages
conda init --reverse # And remove installation folder to uninstall miniconda
```

Here are some frequently used pacakges.
Enable `conda-forge` channel to include a large set of community-maintained packages.

```bash
# System utility
conda install -c conda-forge git tmux htop
# Storage related
conda install -c conda-forge rsync rclone git-annex -c sshockwave bindfs gocryptfs lux
# Data science
conda install -c conda-forge numpy scipy tqdm
conda install pytorch torchvision torchaudio cudatoolkit=11.3 -c pytorch
# Web development
conda install -c conda-forge nodejs
# Multimedia
conda install -c conda-forge ffmpeg
# Build tools
conda install -c conda-forge cxx-compiler make gdb
```
### Containers
Docker is a typical example of container applications.
