# ClamUI v0.1.5

CLI pipeline, security hardening, and broad compatibility improvements.

## Highlights

### Full CLI Subcommand Pipeline
ClamUI can now be driven entirely from the terminal. New subcommands: `scan`, `status`, `history`, `quarantine`, `profile`, and `apply-preferences`.

### Security Fixes
- **CVE-2026-31899** (cairosvg decompression-bomb bypass on redirects) — bumped to cairosvg >= 2.9.0
- Bumped urllib3, numpy, and other dependencies to patched versions
- Added **CodeQL** static analysis and **Dependabot** to CI

### Privacy-Safe Logs
Scan logs no longer persist file-identifying data. Existing logs are migrated on startup.

## What's New

- Full CLI subcommand pipeline for headless ClamAV management (`scan`, `status`, `history`, `quarantine`, `profile`, `apply-preferences`)
- Dolphin (KDE Plasma 6) file manager integration
- Force Adwaita icon theme for cross-runtime icon consistency
- EICAR self-test now uses clamscan for reliable detection
- Improved update rate-limit reporting with refreshed translations

## Compatibility

- **Dropped Python 3.10** — minimum is now Python 3.11
- Ubuntu 22.04 / Pop!_OS 22.04 compatibility for PyGObject < 3.50 and GLib 2.72
- Ensured broad libadwaita 1.1+ compatibility

## Bug Fixes

- Fixed tray updates and window toggle behavior
- Fixed duplicate/un-clearable `DatabaseCustomURL` lines in freshclam.conf
- Hardened preferences save flow against missing widgets
- Improved preferences save authentication UX
- Fixed host-aware config check for clamd availability in Flatpak
- Handle ClamAV runtime warnings and daemon exclusion patterns
- Fixed thread safety, resource cleanup, and integration bugs

## CI & Infrastructure

- Switched CI to `uv` for faster builds
- Added CVE dependency scanning and Dependabot
- Added CodeQL and dependency review workflows
- Coverage is now opt-in for local `pytest` runs (faster default)

## Install

**Flathub** (recommended):
```
flatpak install flathub io.github.linx_systems.ClamUI
```

**AppImage**: Download from the [Releases page](https://github.com/linx-systems/clamui/releases/tag/v0.1.5)

**From source**:
```bash
git clone https://github.com/linx-systems/clamui.git
cd clamui && uv sync && uv run clamui
```
