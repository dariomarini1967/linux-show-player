<p align="center">
    <img src="https://github.com/FrancescoCeruti/linux-show-player/blob/develop/dist/linuxshowplayer.png?raw=true" alt="Logo" width="100" height=100>
</p>
<h1 align="center">Linux Show Player</h1>
<h3 align="center">Cue player for stage productions</h3>

<p align="center">
    <a href="https://github.com/FrancescoCeruti/linux-show-player/blob/master/LICENSE"><img alt="License: GPL" src="https://img.shields.io/badge/license-GPL-blue.svg"></a>
    <a href="https://github.com/FrancescoCeruti/linux-show-player/releases/latest"><img src="https://img.shields.io/github/release/FrancescoCeruti/linux-show-player.svg?maxAge=2592000" alt="GitHub release" /></a>
    <a href="https://github.com/FrancescoCeruti/linux-show-player/releases"><img src="https://img.shields.io/github/downloads/FrancescoCeruti/linux-show-player/total.svg?maxAge=2592000" alt="Github All Releases" /></a>
    <a href="https://sonarcloud.io/summary/new_code?id=FrancescoCeruti_linux-show-player"><img src="https://sonarcloud.io/api/project_badges/measure?project=FrancescoCeruti_linux-show-player&metric=alert_status" alt="Quality Gate Status"></a>
    <a href="https://gitter.im/linux-show-player/linux-show-player"><img src="https://img.shields.io/gitter/room/nwjs/nw.js.svg?maxAge=2592000" alt="Gitter" /></a>
    <a href="https://github.com/ambv/black"><img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black"></a>
</p>

---

Linux Show Player, LiSP for short, is a free cue player, primarily intended for sound-playback during stage productions. 
The ultimate goal is to provide a complete playback software for musical plays, theatre shows, and similar.

For bugs and requests you can open an issue on the GitHub issues tracker; for support, discussions, and anything else 
you should use the [discussion](https://github.com/FrancescoCeruti/linux-show-player/discussions) section on GitHub
or the [gitter/matrix](https://gitter.im/linux-show-player/linux-show-player) chat.

Linux Show Player is currently developed and tested for **GNU/Linux** only.<br>
_The core components (Python, GStreamer and Qt) are multi-platform, thus in future - despite the name - LiSP might get ported to other platforms._

---

## 🧑‍💻 Installation

You can find the full instructions in the <a href="https://linux-show-player-users.readthedocs.io/en/latest/installation.html">user manual</a>.

### 📦 Flatpak

You can get the latest **development** builds here:
 * [Master](https://github.com/FrancescoCeruti/linux-show-player/releases/tag/ci-master) - Generally stable
 * [Development](https://github.com/FrancescoCeruti/linux-show-player/releases/tag/ci-develop) - Preview features, might be unstable and untested

### 🐧 From your distribution repository

For some GNU/Linux distributions you can install a native package.<br>
Keeping in mind that it might not be the latest version, you can find a list on [repology.org](https://repology.org/metapackage/linux-show-player).

---

## 📖 Usage

The user manual can be [viewed online](http://linux-show-player-users.readthedocs.io/en/latest/index.html)

### ⌨️ Command line:

```
usage: linux-show-player [-h] [-f [FILE]] [-l {debug,info,warning}]
                         [--locale LOCALE]

Cue player for stage productions.

optional arguments:
  -h, --help            show this help message and exit
  -f [FILE], --file [FILE]
                        Session file to open
  -l {debug,info,warning}, --log {debug,info,warning}
                        Change output verbosity. default: warning
  --locale LOCALE       Force specified locale/language
```

### Notes by Dario Marini

- poetry must be installed locally forcing version 1.8.2, command is
pip install poetry==1.8.2
