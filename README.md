# DevOps

## Platforms
### Rootless Linux with Conda
The rootless mode is recommended for most scenarios since it can be used on shared servers and does no harm to the system.
Scripts are built around [conda](https://conda.io) because it:
* is a rootless package manager that neatly installs and removes binaries;
* comes with all the dependencies and thus works on most linux distributions;
* uses environments to separate different installations of packages;
* supports installing self-compiled binaries;
* is actively maintained by the data science community.

#### Conda Installation
To start using conda, the installation file has to be downloaded to the host.
See the [doc](https://docs.conda.io/en/latest/miniconda.html) for more information.

```bash
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh -O miniconda.sh
# Or use curl
# curl https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh > miniconda.sh
# Alternative downloads:
# https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-aarch64.sh

PREFIX="${HOME}/miniconda3"
sh miniconda.sh -b -p "${PREFIX}" # Install in silent mode
source ${PREFIX}/bin/activate # Activate conda in the current shell
conda init # Modify the bash init scripts to activate conda on startup
conda config --set auto_stack 1 # Stack base so that the common utilities are available
```

Common configurations in `~/.condarc`:
```yaml
channels:
  - sshockwave
  - defaults
```

#### Conda Cheatsheet
Conda uses the idea of isolated environments, each of which is contained in a single folder.
Some commands below can be paired with `-n <env_name>` or `-p <env_path>`
to specify the exact environment to operate on.
```bash
conda create -n myenv # Create an environment
conda activate myenv # Enter the environment
conda install python=3.10 -c <channel> # Install packages
conda remove python # Remove packages
conda deactivate # Exit the environment
conda info --envs # List all envs
conda remove -n myenv --all # Remove the environment
conda env export --from-history # Export manually installed packages
```

#### Conda Uninstallation
```bash
conda init --reverse
rm ~/.conda -r
rm ${HOME}/miniconda3 -r # Or other locations of installation
rm ~/.condarc # Optionally remove the config file
```

Here are some frequently used pacakges.
Most of them require the `conda-forge` channel.

```bash
# System utility
conda install git tmux htop vim
# Storage related
conda install rsync rclone git-annex bindfs gocryptfs lux
# Data science
conda install numpy scipy tqdm
conda install -c pytorch pytorch cudatoolkit=11.3
# Web development
conda install nodejs
# Multimedia
conda install ffmpeg
# Build tools
conda install cxx-compiler make gdb
```
### Containers
Docker is a typical example of container applications.

Template `docker-compose.yml`:
```yaml
version: "3.8"
networks:
  net1:
services:
  nginx:
    container_name: nginx
    image: nginx:latest
    environment:
      - PUID=1026
      - PGID=100
      - TZ=Asia/Shanghai
    volumes:
      - /host/path:/container/path:ro
      - /var/run/docker.sock:/var/run/docker.sock
    ports:
      - 8080:80 # host_port:container_port
    restart: unless-stopped
    devices:
      - /dev/dri:/dev/dri
    mem_limit: 3g
    depends_on:
      - web
    networks:
      - net1
    extra_hosts:
      - host.docker.internal:host-gateway
    command: []
  web:
    image: nginx
```

### Browsers
Sandbox applications based on JavaScript or WebAssembly.

Bypassing anti-selenium check:
```python
option = webdriver.ChromeOptions()
option.add_experimental_option("excludeSwitches", ["enable-automation"])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=option)
```
### WSL
### Web
Nginx example configuration: https://www.nginx.com/resources/wiki/start/topics/examples/full/
## Network Settings
### Mirrors and Proxies
For the highlighting of these config files,
see [the list of GitHub Highlight Languages](https://github.com/github/linguist/blob/master/lib/linguist/languages.yml).

<details>
<summary>apt</summary>

```
Acquire::http::proxy "http://127.0.0.1:10809/";
Acquire::https::proxy "https://127.0.0.1:10809/";
```

</details>

<details>
<summary>wget</summary>

```wgetrc
use_proxy=yes
http_proxy=172.23.96.1:20809
https_proxy=172.23.96.1:20809
```

</details>

<details>
<summary>go</summary>

See https://goproxy.io/zh/.
```bash
export GOPROXY=https://proxy.golang.com.cn,direct
```

</details>

<details>
<summary>conda</summary>

There are available mirrors.
See https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/ for more details.
```yaml
channels:
  - defaults
show_channel_urls: true
default_channels:
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/r
  - https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  msys2: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  bioconda: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  menpo: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  pytorch-lts: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.tuna.tsinghua.edu.cn/anaconda/cloud
```

Proxies:
```yaml
proxy_servers:
    http: http://user:pass@corp.com:8080
    https: https://user:pass@corp.com:8080
```

</details>

<details>
<summary>git</summary>

```gitconfig
[http]
        proxy = http://172.22.240.1:7890
```

</details>

<details>
<summary>pip / PyPI</summary>

Temporary mirror:
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple <some-package>
```

Persistent mirror:
```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

Proxy:
```bash
pip install <some-package> --proxy scheme://[user:passwd@]proxy.server:port
```

</details>
