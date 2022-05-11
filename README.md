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
conda config --set auto_stack 1 # Stack base so that the common utilities are available
```

Useful mirrors:
* https://mirror.tuna.tsinghua.edu.cn/help/anaconda/

Common configurations in `~/.condarc`:
```yaml
channels:
  - sshockwave
  # Enable `conda-forge` channel to include a large set of community-maintained packages.
  - conda-forge
  - defaults
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
```

Uninstalling miniconda:
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
conda install -c pytorch pytorch torchvision torchaudio cudatoolkit=11.3
# Web development
conda install nodejs
# Multimedia
conda install ffmpeg
# Build tools
conda install cxx-compiler make gdb
```
### Containers
Docker is a typical example of container applications.
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
To mount another disk on WSL startup, add `/etc/wsl.conf`: 
```ini
[boot]
command="bash /etc/bootup.sh"
```
and create `/etc/bootup.sh`(or anywhere you like):
```bash
#!/bin/bash
# Needed to enable WSL interop in startup script
# See https://github.com/microsoft/wsl/issues/8056
for socket in /run/WSL/*; do
   if [ "$socket" == "/run/WSL/1_interop" ]
   then continue
   fi
   if ss -elx | grep -q "$socket"; then
      export WSL_INTEROP=$socket
   fi
done
# Mount physical disk
# --vhd option is enabled in WSL from Microsoft Store
# See https://docs.microsoft.com/en-us/windows/wsl/wsl2-mount-disk#mount-a-vhd-in-wsl
WSL_INTEROP=/run/WSL/10_interop /mnt/c/Windows/system32/wsl.exe --mount --vhd "C:\\Users\\sshockwave\\Softwares\\Linux\\home.vhdx" --bare
mount /dev/sdd /home
```
## Proxy Settings
[GitHub language highlight file](https://github.com/github/linguist/blob/master/lib/linguist/languages.yml)
### apt
Proxy setting:
```
Acquire::http::proxy "http://127.0.0.1:10809/";
Acquire::https::proxy "https://127.0.0.1:10809/";
```
### wget
```wgetrc
use_proxy=yes
http_proxy=172.23.96.1:20809
https_proxy=172.23.96.1:20809
```
### go
See https://goproxy.io/zh/.
```bash
export GOPROXY=https://proxy.golang.com.cn,direct
```
