# AGENTS.md — ClamUI AI Assistant Guide

> Canonical AI-assistant guide for this repository. Also read by Claude Code, Cursor, Aider, Continue, and Zed via the AGENTS.md convention. `CLAUDE.md` is a stub that redirects here — keep updates to this file.

## Project Overview

ClamUI is a modern Linux desktop application providing a graphical user interface for ClamAV antivirus. Built with **PyGObject**, **GTK4**, and **libadwaita** for native GNOME integration.

**Key Facts:**

- Python 3.11+ required
- GTK4/libadwaita UI (targets libadwaita 1.1+ for Ubuntu 22.04 / Pop!\_OS 22.04 baseline)
- ClamAV integration via subprocess (clamscan, clamdscan, freshclam)
- Distributed as native Debian package, AppImage, and Flatpak
- VirusTotal integration for enhanced threat analysis
- Translations: de, en, fr, it, zh_CN (see `po/LINGUAS`)
- MIT licensed

## Repository Structure (top level)

```
clamui/
├── src/                    Application source — read per-dir AGENTS.md (below)
│   ├── main.py             Application entry point
│   ├── app.py              Adw.Application (lifecycle, views, tray)
│   ├── cli/                CLI entry points + command router
│   ├── core/               Business logic, no UI dependencies
│   ├── profiles/           Scan profile management
│   └── ui/                 GTK4/Adwaita UI components
├── tests/                  Mirrors src/ (core/, ui/, profiles/, integration/, e2e/)
├── docs/                   Developer + user docs (table below)
│   ├── architecture/       Architectural notes (e.g. tray-subprocess)
│   └── user-guide/         End-user pages (getting-started, scanning, quarantine, …)
├── po/                     Translations (de, en, fr, it, zh_CN) + POTFILES.in, clamui.pot
├── scripts/                Dev + packaging scripts (local-run, update-pot, nemo actions, hooks/)
├── appimage/               AppImage build (build-appimage.sh)
├── flathub/                Flatpak manifest + generated Python deps
├── debian/                 Debian packaging
├── data/                   Desktop integration (.desktop, nemo_action, metainfo.xml)
├── icons/                  Application icons
├── website/                Astro marketing site
├── planning/, thoughts/    Internal planning / AI-tooling context snapshots
└── pyproject.toml          Project config + dependencies
```

### Hierarchical context docs (read the nearest one before editing)

Each source subdirectory has a concise local `AGENTS.md` with scope-specific architectural framing — tighter than this root file. When working inside one of these directories, read its `AGENTS.md` first:

- [`src/core/AGENTS.md`](src/core/AGENTS.md) — business-logic layer (no UI deps)
- [`src/core/quarantine/AGENTS.md`](src/core/quarantine/AGENTS.md) — SQLite quarantine subsystem
- [`src/ui/AGENTS.md`](src/ui/AGENTS.md) — GTK4/Adwaita UI layer
- [`src/ui/scan/AGENTS.md`](src/ui/scan/AGENTS.md) — scan workflow (coordinator pattern, replaces monolithic `scan_view.py`)
- [`src/ui/preferences/AGENTS.md`](src/ui/preferences/AGENTS.md) — modular preferences pages

## Architecture Documentation

For detailed technical documentation on specific architectural patterns, see the `docs/` directory:

| Document                                                                       | Description                                         |
| ------------------------------------------------------------------------------ | --------------------------------------------------- |
| [`docs/architecture/tray-subprocess.md`](docs/architecture/tray-subprocess.md) | System tray subprocess architecture (GIO D-Bus/SNI) |
| [`docs/CONFIGURATION.md`](docs/CONFIGURATION.md)                               | Comprehensive configuration reference               |
| [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)                                   | Development environment setup                       |
| [`docs/INSTALL.md`](docs/INSTALL.md)                                           | Installation guide                                  |
| [`docs/SCAN_BACKENDS.md`](docs/SCAN_BACKENDS.md)                               | Scan backend options and performance                |
| [`docs/SIGNING.md`](docs/SIGNING.md)                                           | Package signing and verification                    |
| [`docs/TROUBLESHOOTING.md`](docs/TROUBLESHOOTING.md)                           | Common issues and solutions                         |
| [`docs/TRANSLATING.md`](docs/TRANSLATING.md)                                   | Translation contributing guide                      |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)                                     | End-user documentation                              |

### System Tray Subprocess Architecture

**Location**: [`docs/architecture/tray-subprocess.md`](docs/architecture/tray-subprocess.md)

ClamUI uses a subprocess architecture for system tray integration:

- **Main process** (GTK4): `ClamUIApp` and `TrayManager`
- **Subprocess** (GIO D-Bus): `TrayService` using StatusNotifierItem protocol + libdbusmenu
- **IPC**: JSON messages over stdin/stdout pipes

The subprocess uses pure GIO D-Bus (GTK-agnostic) to implement the SNI protocol, with `Dbusmenu` (GLib API) for context menus. The documentation includes:

- Runtime architecture diagrams showing process boundaries and threading models
- Complete IPC protocol specification (commands, events, message formats)
- Sequence diagrams for startup, status updates, and menu actions
- Component relationships between `app.py`, `tray_manager.py`, `tray_service.py`, and `tray_icons.py`
- Security considerations and troubleshooting guides

**When to reference this:**

- Implementing features that update the system tray (status, progress, icons)
- Debugging IPC communication issues between main app and tray
- Understanding why certain operations require thread-safe callbacks
- Contributing to tray-related code in `src/ui/tray_*.py`

## Development Commands

### Setup

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
    libgirepository-2.0-dev libcairo2-dev pkg-config python3-dev clamav

# Build dependencies for Pillow (tray icon support)
sudo apt install libjpeg-dev zlib1g-dev

# Install Python dependencies with uv
uv sync --dev

# Install git hooks (REQUIRED)
./scripts/hooks/install-hooks.sh

# Run from source
uv run clamui
```

**Important:** The pre-commit hook is **required** for development. It prevents absolute `src.*` imports which break when ClamUI is installed as a Debian package. See [Import Conventions](#import-conventions-package-compatibility) for details.

### Testing

```bash
# Run full test suite (fast local default, no coverage)
pytest

# Run specific test file
pytest tests/core/test_scanner.py -v

# Run with coverage report
pytest --cov=src --cov-report=term-missing

# Run only core tests (faster)
pytest tests/core -v

# Skip e2e tests (CI default)
pytest --ignore=tests/e2e
```

### Linting

```bash
# Check code style
uv run ruff check src/ tests/

# Check formatting
uv run ruff format --check src/ tests/

# Auto-fix issues
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/
```

Important: Always run `uv run ruff format src/ tests/` and `uv run ruff check --fix` before committing to ensure code consistency.

## Code Patterns & Conventions

### Import Conventions (Package Compatibility)

**Always use relative imports** within the `src/` package to ensure compatibility when installed as `clamui`:

```python
# CORRECT - relative imports (work in both development and installed)
from ..core.clipboard import copy_to_clipboard
from .view_helpers import create_empty_state

# WRONG - absolute src imports (break when installed)
from src.core.clipboard import copy_to_clipboard
```

The package is installed as `clamui`, not `src`. Absolute `src.*` imports only work during development but fail when installed via pip/deb/flatpak.

### Internationalization (i18n)

All user-facing strings must be translatable using gettext. The i18n module is at `src/core/i18n.py`.

**Import pattern:**

```python
from ..core.i18n import _, ngettext
```

**Simple strings:**

```python
label.set_text(_("Scan Complete"))
```

**Format strings (NEVER use f-strings inside `_()`):**

```python
# CORRECT
label.set_text(_("Found {count} threats").format(count=n))

# WRONG - xgettext cannot extract f-strings
label.set_text(_(f"Found {n} threats"))
```

**Plurals:**

```python
msg = ngettext("{n} file scanned", "{n} files scanned", count).format(n=count)
```

**Module-level constants (deferred translation):**

```python
from ..core.i18n import N_
ITEMS = [N_("Scan"), N_("Update")]  # Mark for extraction only
# At display time:
label.set_text(_(item))
```

**Do NOT translate:**

- Logger messages (`logger.debug/info/warning/error`)
- Developer-facing exception messages
- CSS class names, D-Bus paths, settings keys, technical identifiers
- Shell commands shown to users (e.g., `"sudo apt install clamav"`)

**After adding/changing translatable strings:**

Run `./scripts/update-pot.sh` to regenerate the POT template. To add a new language, see [`docs/TRANSLATING.md`](docs/TRANSLATING.md).

### Async Operations (GTK Thread Safety)

All long-running operations use background threads with `GLib.idle_add()` for UI updates:

```python
def scan_async(self, path: str, callback: Callable[[ScanResult], None]) -> None:
    def scan_thread():
        result = self.scan_sync(path)
        GLib.idle_add(callback, result)  # Schedule callback on main thread

    thread = threading.Thread(target=scan_thread, daemon=True)
    thread.start()
```

### Scanner Type System

Scanner results use a shared type system defined in `scanner_types.py`:

```python
from src.core.scanner_types import ScanStatus, ThreatDetail, ScanResult

# ScanStatus enum: CLEAN, INFECTED, ERROR, CANCELLED
# ThreatDetail dataclass for structured threat information
# ScanResult dataclass with computed properties (is_clean, has_threats)
```

### Threat Classification

Threats are classified by severity and category using `threat_classifier.py`:

```python
from src.core.threat_classifier import classify_threat, ThreatSeverity

severity = classify_threat("Trojan.GenericKD")  # Returns ThreatSeverity.HIGH
# ThreatSeverity: CRITICAL, HIGH, MEDIUM, LOW
```

### Input Sanitization

Always sanitize user input before logging to prevent log injection attacks:

```python
from src.core.sanitize import sanitize_log_line, sanitize_path_for_display

# Removes ANSI escape sequences, control characters, Unicode bidirectional overrides
safe_output = sanitize_log_line(clamav_output)
safe_path = sanitize_path_for_display(user_provided_path)
```

### Path Validation

Validate paths before file operations, especially with user input:

```python
from src.core.path_validation import validate_path, check_symlink_safety

is_valid, error = validate_path(user_path)
is_safe, target = check_symlink_safety(symlink_path)
```

### Dataclasses for Results

Use `@dataclass` for structured data with properties for computed values:

```python
@dataclass
class ScanResult:
    status: ScanStatus
    infected_files: list[str]
    infected_count: int

    @property
    def is_clean(self) -> bool:
        return self.status == ScanStatus.CLEAN
```

### Error Handling Pattern

Return tuples of `(success: bool, error_or_value: Optional[str])`:

```python
def check_clamav_installed() -> Tuple[bool, Optional[str]]:
    # Returns (True, version_string) or (False, error_message)
```

### Flatpak Support

Commands that execute on the host system must be wrapped:

```python
from src.core.flatpak import wrap_host_command, is_flatpak

cmd = wrap_host_command(["clamscan", "--version"])
# In Flatpak: ['flatpak-spawn', '--host', 'clamscan', '--version']
# Native: ['clamscan', '--version']
```

Additional Flatpak utilities in `flatpak.py`:

- `get_clamav_database_dir()` - Get ClamAV database directory for Flatpak
- `ensure_clamav_database_dir()` - Create database directory if needed
- `ensure_freshclam_config()` - Generate freshclam.conf with correct paths
- `format_flatpak_portal_path()` - Format paths from Flatpak portal

### GTK4 Widget Patterns

- Inherit from appropriate base class (`Gtk.Box`, `Adw.PreferencesWindow`, etc.)
- Use `gi.require_version()` before importing
- Set CSS classes via `add_css_class()`

### libadwaita Version Compatibility

Targets **libadwaita 1.1+** (Ubuntu 22.04 / Pop!\_OS 22.04 baseline). **Do not use APIs introduced after 1.1.** Runtime fallbacks for missing APIs live in `src/ui/compat.py`. The `adw-compat` skill has the exhaustive API migration reference.

| Avoid (1.2+)                     | Use instead (1.0+)                                                            |
| -------------------------------- | ----------------------------------------------------------------------------- |
| `Adw.PasswordEntryRow`           | `create_password_entry_row()` from `preferences/base.py`                      |
| `Adw.SpinRow`                    | `create_spin_row()` from `preferences/base.py` (returns `(row, spin_button)`) |
| `Adw.Dialog` / `Adw.AlertDialog` | `Adw.Window` (see pattern below)                                              |

**Dialog pattern (`Adw.Window` + `set_content`/`set_default_size`/`close-request`):**

```python
class MyDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window | None = None):
        super().__init__()
        self.set_title("Dialog Title")
        self.set_default_size(400, 300)   # not set_content_width/height
        self.set_modal(True)
        self.set_deletable(True)          # not set_can_close
        self.set_content(content_widget)  # not set_child
        if parent:
            self.set_transient_for(parent)
        self.connect("close-request", self._on_close_request)  # not "closed"
```

Present with `dialog.set_transient_for(parent); dialog.present()` — **not** `dialog.present(parent)` (that's 1.5+).

**Compatibility helpers (`src/ui/preferences/base.py`):**

```python
from .base import create_password_entry_row, create_spin_row

api_key_row = create_password_entry_row("API Key")
row, spin_button = create_spin_row(title="Max File Size (MB)", min_val=0, max_val=4000, step=1)
widgets_dict["MaxFileSize"] = spin_button  # store SpinButton, not row
group.add(row)
```

### Icon Usage (Adwaita Only)

Always use standard Adwaita symbolic icons. Never use:

- Application-specific icons (e.g., `org.gnome.Nautilus-symbolic`)
- KDE/Breeze icons
- Non-standard icon names

**Safe Adwaita icons for common use cases:**

- File/folder: `folder-symbolic`, `folder-open-symbolic`
- Info: `dialog-information-symbolic`
- Warning: `dialog-warning-symbolic`
- Error: `dialog-error-symbolic`
- Settings: `preferences-system-symbolic`
- Security: `security-high-symbolic`, `security-medium-symbolic`

Reference: https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/named-icons.html

### Thread Locks

Use `threading.Lock()` for shared state in managers:

```python
class QuarantineManager:
    def __init__(self):
        self._lock = threading.Lock()

    def quarantine_file(self, path: str) -> QuarantineResult:
        with self._lock:
            # Thread-safe operations
```

### Modular Preferences Pattern

Preferences pages inherit from `PreferencesPageMixin`:

```python
from src.ui.preferences.base import PreferencesPageMixin

class DatabasePage(PreferencesPageMixin):
    @classmethod
    def create_page(cls, parent_window):
        return cls(transient_for=parent_window)
```

### Reusable Export Dialog Pattern

Use `FileExportHelper` for file export dialogs:

```python
from src.ui.file_export import FileExportHelper, FileFilter

FileExportHelper.show_export_dialog(
    filters=[FileFilter(name="CSV Files", extension="csv")],
    initial_name="scan_results.csv",
    content_generator=lambda: format_results_as_csv(result),
    on_success=lambda: show_toast("Export successful")
)
```

### Pagination Pattern

Use `PaginatedListController` for large lists:

```python
from src.ui.pagination import PaginatedListController

controller = PaginatedListController(
    list_box=self.list_box,
    initial_limit=50,
    batch_size=50
)
controller.set_items(items, create_row_func)
```

### VirusTotal Integration Pattern

Use `VirusTotalClient` for threat analysis:

```python
from src.core.virustotal import VirusTotalClient, VTScanStatus

client = VirusTotalClient(api_key)
result = client.scan(file_path)  # Handles rate limiting internally

if result.status == VTScanStatus.FOUND:
    print(f"Detections: {result.positives}/{result.total}")
```

### Secure API Key Storage

Use `KeyringManager` for secure credential storage:

```python
from src.core.keyring_manager import KeyringManager

manager = KeyringManager()
manager.set_api_key("virustotal", api_key)  # Uses system keyring
key = manager.get_api_key("virustotal")
```

## Testing Guidelines

### GTK Mocking (conftest.py)

Tests use centralized GTK mocking from `tests/conftest.py`:

```python
def test_something(mock_gi_modules):
    gtk = mock_gi_modules['gtk']
    from src.ui.some_view import SomeView
    # SomeView can be imported with mocked GTK
```

### Fixtures

- `tmp_path`: Pytest's temporary directory (use for file I/O tests)
- `eicar_file`: EICAR test file for antivirus testing
- `eicar_directory`: Directory with EICAR + clean files
- `mock_scanner`: Pre-configured Scanner mock

### Test File Naming

- Tests mirror source structure: `src/core/scanner.py` -> `tests/core/test_scanner.py`
- Preferences tests: `src/ui/preferences/scanner_page.py` -> `tests/ui/preferences/test_scanner_page.py`
- Prefix test methods with `test_`
- Use descriptive docstrings

### Coverage Requirements

- **Overall minimum**: 50% (fail_under in pyproject.toml)
- **Target coverage**: 80%+ for src/core, 70%+ for src/ui

## Key Modules Reference

### Scanner (`src/core/scanner.py`)

- Supports three backends: `"auto"`, `"daemon"`, `"clamscan"`
- Parses ClamAV exit codes: 0=clean, 1=infected, 2=error
- Uses `scanner_types.py` for result types
- Uses `threat_classifier.py` for threat classification
- Saves scan logs via `LogManager`

### Scanner Types (`src/core/scanner_types.py`)

- `ScanStatus` enum: CLEAN, INFECTED, ERROR, CANCELLED
- `ThreatDetail` dataclass: file_path, threat_name, severity, category
- `ScanResult` dataclass: status, threats, scanned_count, with computed properties

### Threat Classifier (`src/core/threat_classifier.py`)

- `ThreatSeverity` enum: CRITICAL, HIGH, MEDIUM, LOW
- Pattern-based classification for 70+ threat types
- Category mapping (Trojan, Ransomware, Adware, etc.)
- `classify_threat()` and `get_threat_category()` functions

### VirusTotal Client (`src/core/virustotal.py`)

- `VirusTotalClient` class with API v3 support
- SHA256 hash lookups for known files
- File upload for unknown files (up to 32MB)
- Rate limiting (4 requests/minute for free tier)
- Exponential backoff retry logic
- `VTScanStatus` enum: FOUND, NOT_FOUND, QUEUED, ERROR
- `VTScanResult` dataclass with detection details

### Sanitization (`src/core/sanitize.py`)

- `sanitize_log_line()` - Removes ANSI, control chars, null bytes
- `sanitize_path_for_display()` - Safe path display
- Prevents log injection attacks
- Removes Unicode bidirectional overrides

### Path Validation (`src/core/path_validation.py`)

- `validate_path()` - Validates path existence and permissions
- `check_symlink_safety()` - Checks symlink targets
- `validate_drag_drop_paths()` - Validates file manager drops
- `get_path_metadata()` - Extracts file metadata

### ClamAV Detection (`src/core/clamav_detection.py`)

- `check_clamav_installed()` - Check installation and version
- `find_clamav_binary()` - Locate ClamAV executables
- `check_clamd_connection()` - Test daemon connectivity

### Keyring Manager (`src/core/keyring_manager.py`)

- Secure storage using system keyring (GNOME Keyring, KWallet)
- Fallback to settings.json when keyring unavailable
- `get_api_key()`, `set_api_key()`, `delete_api_key()`

### Scheduler (`src/core/scheduler.py`)

- Detects systemd vs cron availability
- Creates systemd user timers or crontab entries
- Validates paths for injection attacks
- Uses `shlex.quote()` for safe command building

### QuarantineManager (`src/core/quarantine/manager.py`)

- Orchestrates `QuarantineDatabase` + `SecureFileHandler`
- Uses `ConnectionPool` for efficient database access
- Verifies file integrity via SHA-256 hashing
- Supports async operations with callbacks

### ProfileManager (`src/profiles/profile_manager.py`)

- Creates default profiles on first run (Quick Scan, Full Scan, Home Folder)
- Validates names, paths, and exclusion patterns
- Supports import/export with duplicate name handling

### ClamUIApp (`src/app.py`)

- Main `Adw.Application` class
- Manages view lifecycle and navigation
- Handles tray integration via subprocess (GIO D-Bus for SNI protocol)
- Implements start-minimized functionality

### Preferences System (`src/ui/preferences/`)

- `PreferencesWindow` - Main window orchestrating all pages
- `PreferencesPageMixin` - Base class with shared utilities
- Individual page classes for each settings category:
  - `BehaviorPage` — close behavior, notifications, tray
  - `DatabasePage` — freshclam settings
  - `ExclusionsPage` — exclusion patterns
  - `OnAccessPage` — on-access scanning
  - `ScannerPage` — clamd configuration
  - `ScheduledPage` — scheduled scans
  - `VirusTotalPage` — VirusTotal API setup
  - `DebugPage` — diagnostics, logging controls
  - `DeviceScanPage` — removable-device scan configuration
  - `SavePage` — save & apply with permission elevation

### UI Helpers (`src/ui/view_helpers.py`)

- `StatusLevel` enum for consistent styling
- `set_status_class()` for status banners
- `create_empty_state()` for empty list states
- Loading indicator helpers

### Pagination (`src/ui/pagination.py`)

- `PaginatedListController` class
- Configurable batch sizes and initial limits
- "Show More"/"Show All" controls
- Used by logs_view.py and quarantine_view.py

### File Export (`src/ui/file_export.py`)

- `FileExportHelper` class
- `FileFilter` dataclass for file type filters
- Async file selection with cancellation
- Error handling and toast notifications

## Configuration & Settings

### Settings Location

- XDG compliant: `~/.config/clamui/settings.json`
- Profiles: `~/.config/clamui/profiles.json`
- Quarantine DB: `~/.local/share/clamui/quarantine.db`
- Quarantine files: `~/.local/share/clamui/quarantine/`
- Logs: `~/.local/share/clamui/logs/`

### Key Settings

```json
{
  "scan_backend": "auto", // "auto", "daemon", "clamscan"
  "start_minimized": false,
  "minimize_to_tray": false,
  "show_notifications": true,
  "exclusion_patterns": [], // Global exclusions
  "virustotal_enabled": false, // VirusTotal integration
  "virustotal_auto_submit": false
}
```

#### Scan Backend Options

`scan_backend` ∈ {`"auto"` (default), `"daemon"`, `"clamscan"`}. Auto prefers clamd when available (instant startup, parallel via `--multiscan`/`--fdpass`), falls back to clamscan (3–10 sec startup, always available). See [`docs/SCAN_BACKENDS.md`](docs/SCAN_BACKENDS.md) for performance tables, daemon setup, and troubleshooting.

## CI/CD Workflows

### test.yml

- Runs on Python 3.11, 3.12, 3.13
- Uses xvfb for headless GTK testing
- Uploads coverage report on Python 3.12

### lint.yml

- Runs Ruff linting and format checking
- Configured rules in pyproject.toml

### build-appimage.yml

- Builds AppImage on push to master, tags, PRs
- Uses ubuntu-24.04 runner
- Uploads AppImage as artifact (7-day retention)

## Security Considerations

1. **Input Sanitization**: Use `sanitize_log_line()` before logging user/external input
2. **Path Validation**: Always validate paths with `validate_path()` before operations
3. **Symlink Safety**: Check symlinks with `check_symlink_safety()` before following
4. **Command Injection**: Use `shlex.quote()` for user-provided paths in shell commands
5. **Scheduler Security**: `_validate_target_paths()` checks for newlines/null bytes
6. **Quarantine Integrity**: SHA-256 hash verification before restore
7. **API Key Storage**: Use `KeyringManager` for secure credential storage
8. **Secrets**: Never commit `.env` files or credentials

## Common Tasks

### Adding a New View

1. Create `src/ui/new_view.py` inheriting from `Gtk.Box` or similar
2. Add view instance in `app.py:do_activate()`
3. Add action in `app.py:_setup_actions()`
4. Add navigation button in `window.py:_create_navigation_buttons()`
5. Write tests in `tests/ui/test_new_view.py`

### Adding a Core Feature

1. Create module in `src/core/`
2. Use dataclasses for results, enums for statuses
3. Implement both sync and async methods
4. Add thread locks for shared state
5. Use `sanitize_log_line()` for any user/external input logging
6. Write comprehensive tests

### Adding a Preferences Page

1. Create `src/ui/preferences/new_page.py` inheriting from `PreferencesPageMixin`
2. Implement `create_page()` class method
3. Add page instantiation in `PreferencesWindow.__init__()`
4. Write tests in `tests/ui/preferences/test_new_page.py`

### Modifying Scan Profiles

1. Default profiles defined in `ProfileManager.DEFAULT_PROFILES`
2. Validation in `_validate_profile()`, `_validate_targets()`, `_validate_exclusions()`
3. Storage in `ProfileStorage` using atomic file writes

## Debugging Tips

1. **GTK Issues**: Check `GLib.idle_add()` usage for thread safety
2. **Flatpak**: Test with `is_flatpak()` detection
3. **ClamAV Not Found**: Check `check_clamav_installed()` in `clamav_detection.py`
4. **Daemon Issues**: Verify clamd socket with `get_clamd_socket_path()`
5. **Test Failures**: Ensure `mock_gi_modules` fixture is used for UI tests
6. **VirusTotal Issues**: Check API key with `KeyringManager`, verify rate limiting
7. **Sanitization Issues**: Check `sanitize.py` for character filtering

## Entry Points (pyproject.toml)

```toml
[project.scripts]
clamui = "src.main:main"
clamui-scheduled-scan = "src.cli.scheduled_scan:main"
clamui-apply-preferences = "src.cli.apply_preferences:main"
```

The `src/cli/` package uses a command router (`router.py`) that dispatches to domain-specific modules: `scan_cmd.py`, `profile_cmd.py`, `quarantine_cmd.py`, `history_cmd.py`, `status_cmd.py`, plus `help_cmd.py` / `output.py` helpers. To add a subcommand, create a `*_cmd.py` module and register it in `router.py`.

## Dependencies

Key runtime dependencies:

- `PyGObject` - GTK4/Adwaita bindings (provided by system/runtime)
- `keyring>=25.0.0` - Secure credential storage
- `Pillow>=10.0.0` - Tray icon generation (composite status badges)
- `cairosvg>=2.7.0` - SVG to PNG conversion for tray icons

**Build dependencies for Pillow (Ubuntu/Debian):**
```bash
sudo apt install libjpeg-dev zlib1g-dev
```

## Flatpak Development

### Flatpak Python Dependencies

Python dependencies for the Flatpak build are managed using:

- **Build dependencies**: `flatpak-pip-generator` from [flatpak-builder-tools](https://github.com/flatpak/flatpak-builder-tools/tree/master/pip)
- **Runtime dependencies**: `req2flatpak` (prefers binary wheels for faster builds)

**Files:**

- `flathub/requirements-build.txt` - Build dependencies (hatchling)
- `flathub/requirements-runtime.txt` - Runtime dependencies with minimum versions
- `flathub/requirements-runtime-pinned.txt` - Pinned versions for req2flatpak
- `flathub/python3-build-deps.json` - Generated build dependencies (commit to git)
- `flathub/python3-runtime-deps.json` - Generated runtime dependencies (commit to git)

**Note:** PyGObject and pycairo are provided by the GNOME runtime and excluded from generation.

### Flatpak-Specific Code

The `src/core/flatpak.py` module handles Flatpak-specific functionality:

- `is_flatpak()` - Detect if running in Flatpak sandbox
- `wrap_host_command()` - Wrap commands for host execution
- `get_clamav_database_dir()` - Get writable database directory
- `ensure_freshclam_config()` - Generate freshclam.conf for Flatpak

### Regenerating Flatpak Dependencies

When dependencies in `pyproject.toml` change:

```bash
# Install the generators
pipx install flatpak-pip-generator
pipx install req2flatpak

# Ensure the GNOME SDK is installed
flatpak install flathub org.gnome.Sdk//49

cd flathub/

# 1. Generate build dependencies (uses flatpak-pip-generator)
flatpak_pip_generator \
    --runtime='org.gnome.Sdk//49' \
    --requirements-file='requirements-build.txt' \
    --output='python3-build-deps' \
    --checker-data

# 2. Update requirements-runtime-pinned.txt with new versions
#    Then generate runtime dependencies for BOTH architectures (x86_64 and aarch64)
req2flatpak \
    -r requirements-runtime-pinned.txt \
    -t 313-x86_64 313-aarch64 \
    -o python3-runtime-deps.json
```

**Note:** The `-t` flag accepts multiple space-separated targets. Using `313-x86_64 313-aarch64` generates a single JSON file with architecture-specific entries for binary wheels and shared entries for pure Python wheels.

### Testing Flatpak Build

```bash
# Build the Flatpak
flatpak-builder --force-clean build-dir flathub/io.github.linx_systems.ClamUI.yml

# Run the built application
flatpak-builder --run build-dir flathub/io.github.linx_systems.ClamUI.yml clamui
```

## AppImage Development

### Prerequisites

```bash
# Install AppImage build tools (Ubuntu/Debian)
sudo apt install wget file patchelf desktop-file-utils libgdk-pixbuf2.0-dev
```

### Building an AppImage

```bash
# Run from project root
./appimage/build-appimage.sh
```

The script:
1. Creates a Python virtual environment with GTK4/libadwaita
2. Bundles all dependencies into an AppDir structure
3. Downloads and uses `linuxdeploy` + `linuxdeploy-plugin-gtk` for GTK runtime bundling
4. Produces `ClamUI-<version>-x86_64.AppImage` (~96 MB)

**Note:** The AppImage bundles Python and GTK4/libadwaita but requires ClamAV to be installed on the host system. ClamAV cannot be bundled as it requires system-level virus database updates.

### Testing the AppImage

```bash
# Make executable and run
chmod +x ClamUI-*-x86_64.AppImage
./ClamUI-*-x86_64.AppImage
```

See `appimage/build-appimage.sh` for detailed build configuration.

---

## Packaging Notes

- Flatpak uses `--filesystem=host` (read-write) for full scanning + quarantine operations.
- Debian packages require Python 3.11+.
- AppImage bundles Python + GTK4/libadwaita (~96 MB); still requires host ClamAV.
- `urllib3>=2.6.3` is pinned for CVE fix (decompression-bomb bypass on redirects).
- See [`RELEASE_NOTES.md`](RELEASE_NOTES.md) and [`SECURITY.md`](SECURITY.md) for historical security-hardening changes and current advisories.
