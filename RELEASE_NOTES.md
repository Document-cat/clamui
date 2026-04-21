# ClamUI v0.1.7

System security audit dashboard, Flatpak hardening, AppImage delta updates, and tray reliability.

## Highlights

### System Security Audit

A new dashboard that reviews the overall security posture of the host, not just ClamAV:

- Firewall presence and rule health (with distro-specific launch buttons for GUI firewall tools)
- SSH daemon configuration and exposure
- Open-port review (any open ports flagged as warning, risky ports as fail)
- MAC framework status (AppArmor / SELinux)
- Rootkit scanner availability
- ClamAV health (database freshness, daemon status)
- In-app notifications when issues are found, with info links to each check

### Packaging & Distribution

- **AppImage delta updates** via zsync — future updates pull only changed bytes instead of re-downloading ~96 MB
- **Flatpak-aware folder/dialog/launch paths** — "Open folder" and file-manager handoffs now work correctly from inside the Flatpak sandbox
- **Restart ClamAV services** after config changes so the daemon picks up new settings automatically
- **Fedora clamd detection fixes** for hosts where clamd and freshclam are packaged separately

### Internationalization

- **French** and **Italian** translations added (community contributions — thanks [@robinguy44](https://github.com/robinguy44) and [@albanobattistella](https://github.com/albanobattistella))
- **Chinese (zh_CN)** fuzzy strings refreshed (thanks [@Marksonthegamer](https://github.com/Marksonthegamer))
- **German** strings re-synced against the latest POT template
- **Language override** preference — pick the interface language regardless of the system `LANG` setting

### Security Hardening

- Addressed **OWASP audit findings** across scanner, updater, and logging paths
- Path-validation hardening (`ValueError` on resolve is now caught instead of propagating)
- Pango markup escaped in widget titles and subtitles to prevent markup injection from filenames
- Bumped **pytest >=9.0.3** (CVE-2025-71176), refreshed **cryptography** and **certifi** pins

### Reliability & UX

- Scan detail view UX improvements and cleaner GUI shutdown sequence
- Non-UTF-8 filenames no longer crash scans on Linux
- Non-fatal LibClamAV errors no longer cause hard scan failures
- Progress bar clamped to 100% with an overflow indicator on underestimated scans
- Plasma tray watcher registration timing fix — tray icon now appears reliably on KDE
- `StartupWMClass` added to desktop files so window managers match windows to the right application
- Deferred panel data loading and shared `LogManager` across views for faster startup
- Config-save path repairs and Flatpak write support

## What's Missing Compared to v0.1.6 Notes

None — this is a strict superset of v0.1.6 plus the new features above.

## Install

**Flathub** (recommended):
```bash
flatpak install flathub io.github.linx_systems.ClamUI
```

**AppImage**: Download the `ClamUI-0.1.7-x86_64.AppImage` from the [Releases page](https://github.com/linx-systems/clamui/releases/tag/v0.1.7). Existing AppImages can delta-update via zsync.

**GitHub Release**: Download from the [Releases page](https://github.com/linx-systems/clamui/releases/tag/v0.1.7)

**From source**:
```bash
git clone https://github.com/linx-systems/clamui.git
cd clamui && uv sync && uv run clamui
```

## Contributors

Thanks to everyone who contributed code, translations, and bug reports for this release. See the [full commit log](https://github.com/linx-systems/clamui/compare/v0.1.6...v0.1.7) for details.
