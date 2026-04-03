# ClamUI v0.1.6

Security hardening, daemon-scanner fixes, and release pipeline updates.

## Highlights

### Scanner Reliability
- Fixed daemon scanning behavior that could miss EICAR detections when `--fdpass` was used
- Corrected clamd streaming and size-limit unit handling
- Restored `clamdscan` detection for live-progress scans
- Improved handling for non-UTF-8 scanner output

### Security Hardening
- Validated destination paths in the privileged config helper
- Eliminated shell injection risk in updater force-update flows
- Addressed additional static-analysis and CodeQL findings

### Dependencies and CI
- Refreshed dependency pins including `cryptography`, `requests`, `numpy`, `Pillow`, `charset-normalizer`, and `more-itertools`
- Added a dedicated dependency-audit GitHub Actions workflow
- Updated GPG import action usage for Node 24 compatibility

## User-Facing Fixes

- Fixed tray profile selection navigation
- Clarified follow-up quality fixes across scanner and release paths

## Install

**Flathub** (recommended):
```bash
flatpak install flathub io.github.linx_systems.ClamUI
```

**GitHub Release**: Download from the [Releases page](https://github.com/linx-systems/clamui/releases/tag/v0.1.6)

**From source**:
```bash
git clone https://github.com/linx-systems/clamui.git
cd clamui && uv sync && uv run clamui
```
