# Copilot Instructions for Linux Show Player (LiSP)

## Project Overview
Linux Show Player (LiSP) is a cue player for stage productions, built primarily for GNU/Linux. It uses Python, GStreamer, and Qt for its core components. The architecture is modular, with clear separation between backend logic, UI, plugins, and command handling.

## Key Components
- `backend/`: Core audio/media logic (e.g., `backend.py`, `media.py`, `waveform.py`).
- `ui/`: Main Qt-based GUI components and utilities.
- `core/`: Shared infrastructure (configuration, plugin management, registries).
- `command/`: Cue and command modeling, stack management.
- `plugins/`: Extensible features; each plugin in its own subfolder.
- `cues/`, `layout/`: Cue types and layout logic.
- `scripts/flatpak/`: Flatpak build scripts and packaging logic.

## Developer Workflows
- **Run the app:** Use the main entry point (`lisp/main.py`).
- **Build Flatpak:** Use `scripts/flatpak/build-flatpak.sh` (requires Flatpak, ostree, flatpak-builder, Python ≥3.9).
- **Python packaging:** Managed via Poetry (`pyproject.toml`, `poetry.lock`).
- **Testing:** No standard test folder; tests may be manual or ad-hoc.
- **Debugging:** Use the `-l {debug,info,warning}` CLI flag for logging level.

## Conventions & Patterns
- **Plugin architecture:** Plugins are loaded dynamically from `plugins/` and registered via `core/plugins_manager.py`.
- **Configuration:** Centralized in `core/configuration.py` and `default.json` files.
- **Cue modeling:** Cues are defined in `cues/` and managed via factories and models.
- **UI:** All Qt widgets and dialogs are in `ui/`.
- **Internationalization:** Managed in `i18n/` (with `.ts` and `.qm` files).
- **Code style:** Follows [Black](https://github.com/ambv/black) formatting.

## Integration Points
- **GStreamer:** Used for audio/media playback (see `backend/audio_utils.py`).
- **Qt:** All UI logic (see `ui/` and `main.py`).
- **Flatpak:** Packaging scripts in `scripts/flatpak/`.

## Examples
- To add a new plugin: create a subfolder in `plugins/`, implement the plugin class, and register it in `core/plugins_manager.py`.
- To add a new cue type: extend models in `cues/`, update factories as needed.
- To patch Flatpak build: edit `scripts/flatpak/patch-manifest.py` or related scripts.

## References
- Main documentation: [`README.md`](../README.md)
- Flatpak build docs: [`scripts/flatpak/README.md`](../scripts/flatpak/README.md)
- User manual: [linux-show-player-users.readthedocs.io](https://linux-show-player-users.readthedocs.io/en/latest/index.html)

---
For questions, see the [GitHub Discussions](https://github.com/FrancescoCeruti/linux-show-player/discussions) or [Gitter chat](https://gitter.im/linux-show-player/linux-show-player).
