# ClamUI Scan Backend Options

ClamUI supports three scan backends, configured in **Preferences > Scanner Settings > Scan Backend** or via `"scan_backend"` in `settings.json`.

## Backend Comparison

| Aspect | Auto (default) | Daemon | Clamscan |
|--------|---------------|--------|----------|
| **Scan startup** | Depends on daemon availability | Instant (<1 sec) | 3-10 sec (loads database) |
| **Memory (idle)** | ~50 MB | 500 MB-1 GB | ~50 MB |
| **Memory (scanning)** | 500 MB-1 GB | 500 MB-1 GB | 500 MB-1 GB |
| **Parallel scanning** | When daemon available | Yes (`--multiscan`) | No |
| **Setup required** | None | Install & run clamd | None |
| **Reliability** | High (auto-fallback) | Requires running daemon | High |

## Auto Mode (Recommended)

Checks daemon availability before each scan (with 60-second cache) and uses the daemon if reachable, otherwise falls back to clamscan. Best for most users.

**Detection process:**
1. Checks if `clamdscan` is installed
2. Pings clamd socket via `clamdscan --ping`
3. If daemon responds: uses daemon backend
4. If unavailable: falls back to clamscan

The availability check result is cached for 60 seconds to avoid repeated socket probes on consecutive scans.

## Daemon Backend

Uses the clamd background service exclusively. Database stays in memory for instant scan startup. Supports `--multiscan` (parallel) and `--fdpass` (file descriptor passing). Scans fail if clamd is not running.

**Best for:** Frequent/scheduled scans, servers, performance-critical environments.

## Clamscan Backend

Uses the standalone `clamscan` command. Loads the database from disk for each scan (3-10 sec overhead). No background service needed.

**Best for:** Occasional scans, minimal installations, troubleshooting.

## Daemon Setup

### Ubuntu/Debian

```bash
sudo apt install clamav-daemon
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon
clamdscan --version  # Verify
```

### Fedora

```bash
sudo dnf install clamd
sudo systemctl enable clamd@scan
sudo systemctl start clamd@scan
```

### Arch Linux

```bash
sudo pacman -S clamav
sudo systemctl enable clamav-daemon
sudo systemctl start clamav-daemon
```

### Flatpak Users

The ClamUI Flatpak bundles ClamAV (clamscan, freshclam) internally. To use the daemon backend, clamd must be installed on the **host system** since it runs as a system service outside the sandbox. ClamUI auto-detects the host daemon.

## Exit Codes

Both backends return standard ClamAV exit codes: `0` = clean, `1` = infected, `2` = error.

## Socket Locations

ClamUI auto-detects the clamd socket by checking:

- `/var/run/clamav/clamd.ctl` (Ubuntu/Debian)
- `/run/clamav/clamd.ctl` (alternative)
- `/var/run/clamd.scan/clamd.sock` (Fedora)

Override with `"daemon_socket_path"` in settings.json, or check `grep "LocalSocket" /etc/clamav/clamd.conf`.

## See Also

- [CONFIGURATION.md](CONFIGURATION.md) - Full settings reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [ClamAV Documentation](https://docs.clamav.net/)
