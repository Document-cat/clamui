# ClamUI Device Scan Page
"""
Device auto-scan preference page for configuring automatic scanning
of newly connected storage devices (USB, external drives, network mounts).

Settings are auto-saved immediately on change (app-level settings,
not clamd.conf), following the same pattern as BehaviorPage.
"""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw

from ...core.i18n import _
from ..compat import create_switch_row
from ..utils import resolve_icon_name
from .base import PreferencesPageMixin, create_spin_row, styled_prefix_icon

# Device type definitions: (setting_value, icon, title, subtitle)
DEVICE_TYPE_ROWS = [
    (
        "removable",
        "media-removable-symbolic",
        "Removable Devices",
        "USB flash drives, SD cards, and other removable media",
    ),
    (
        "external",
        "drive-harddisk-symbolic",
        "External Drives",
        "External HDDs and SSDs (ejectable but not removable media)",
    ),
    (
        "network",
        "network-server-symbolic",
        "Network Mounts",
        "NFS, SMB/CIFS, and SSHFS mounts",
    ),
]


class DeviceScanPage(PreferencesPageMixin):
    """
    Preference page for automatic device scanning.

    Provides settings for:
    - Enabling/disabling device auto-scan
    - Selecting which device types to scan
    - Configuring scan options (size limit, delay, quarantine, etc.)

    All settings auto-save immediately when changed.
    """

    def __init__(self, settings_manager=None):
        """
        Initialize the DeviceScanPage.

        Args:
            settings_manager: SettingsManager instance for persisting settings.
        """
        self._settings_manager = settings_manager

        # Widget references for signal blocking during load
        self._enable_row = None
        self._enable_handler_id = None
        self._type_rows: dict[str, tuple] = {}  # type_key -> (row, handler_id)
        self._max_size_spin = None
        self._max_size_handler_id = None
        self._delay_spin = None
        self._delay_handler_id = None
        self._quarantine_row = None
        self._quarantine_handler_id = None
        self._notify_row = None
        self._notify_handler_id = None
        self._battery_row = None
        self._battery_handler_id = None

    def create_page(self) -> Adw.PreferencesPage:
        """
        Create the Device Scan preference page.

        Returns:
            Configured Adw.PreferencesPage ready to be added to preferences window.
        """
        page = Adw.PreferencesPage(
            title=_("Device Scan"),
            icon_name=resolve_icon_name("drive-removable-media-symbolic"),
        )

        # General group (enable toggle)
        general_group = self._create_general_group()
        page.add(general_group)

        # Device Types group
        types_group = self._create_device_types_group()
        page.add(types_group)

        # Options group
        options_group = self._create_options_group()
        page.add(options_group)

        return page

    def _create_general_group(self) -> Adw.PreferencesGroup:
        """Create the General preferences group with enable toggle."""
        group = Adw.PreferencesGroup()
        group.set_title(_("General"))
        group.set_description(_("Automatically scan storage devices when they are connected"))

        self._enable_row = create_switch_row(icon_name="drive-removable-media-symbolic")
        self._enable_row.set_title(_("Enable Device Auto-Scan"))
        self._enable_row.set_subtitle(_("Scan newly mounted devices in the background"))

        self._enable_handler_id = self._enable_row.connect(
            "notify::active", self._on_enable_changed
        )

        # Load current value
        self._load_switch(
            self._enable_row,
            self._enable_handler_id,
            "device_auto_scan_enabled",
            False,
        )

        group.add(self._enable_row)
        return group

    def _create_device_types_group(self) -> Adw.PreferencesGroup:
        """Create the Device Types preferences group."""
        group = Adw.PreferencesGroup()
        group.set_title(_("Device Types"))
        group.set_description(_("Select which types of devices to scan automatically"))

        current_types = []
        if self._settings_manager:
            current_types = self._settings_manager.get(
                "device_auto_scan_types", ["removable", "external"]
            )

        for type_key, icon, title, subtitle in DEVICE_TYPE_ROWS:
            row = create_switch_row(icon_name=icon)
            row.set_title(_(title))
            row.set_subtitle(_(subtitle))

            handler_id = row.connect("notify::active", self._on_device_type_changed)

            # Block signal, set value, unblock
            row.handler_block(handler_id)
            row.set_active(type_key in current_types)
            row.handler_unblock(handler_id)

            self._type_rows[type_key] = (row, handler_id)
            group.add(row)

        return group

    def _create_options_group(self) -> Adw.PreferencesGroup:
        """Create the Options preferences group."""
        group = Adw.PreferencesGroup()
        group.set_title(_("Options"))
        group.set_description(_("Configure device scan behavior"))

        # Max device size
        max_size_row, self._max_size_spin = create_spin_row(
            title=_("Max Device Size (GB)"),
            subtitle=_("Skip devices larger than this (0 = no limit)"),
            min_val=0,
            max_val=10000,
            step=1,
            page_step=10,
        )
        max_size_row.add_prefix(styled_prefix_icon("drive-harddisk-symbolic"))
        current_max = 32
        if self._settings_manager:
            current_max = self._settings_manager.get("device_auto_scan_max_size_gb", 32)
        self._max_size_spin.set_value(current_max)
        self._max_size_handler_id = self._max_size_spin.connect(
            "value-changed", self._on_max_size_changed
        )
        group.add(max_size_row)

        # Scan delay
        delay_row, self._delay_spin = create_spin_row(
            title=_("Scan Delay (seconds)"),
            subtitle=_("Wait before starting scan after device is mounted"),
            min_val=0,
            max_val=60,
            step=1,
            page_step=5,
        )
        delay_row.add_prefix(styled_prefix_icon("alarm-symbolic"))
        current_delay = 3
        if self._settings_manager:
            current_delay = self._settings_manager.get("device_auto_scan_delay_seconds", 3)
        self._delay_spin.set_value(current_delay)
        self._delay_handler_id = self._delay_spin.connect("value-changed", self._on_delay_changed)
        group.add(delay_row)

        # Auto-quarantine
        self._quarantine_row = create_switch_row(icon_name="user-trash-symbolic")
        self._quarantine_row.set_title(_("Auto-Quarantine Threats"))
        self._quarantine_row.set_subtitle(_("Automatically move detected threats to quarantine"))
        self._quarantine_handler_id = self._quarantine_row.connect(
            "notify::active", self._on_quarantine_changed
        )
        self._load_switch(
            self._quarantine_row,
            self._quarantine_handler_id,
            "device_auto_scan_auto_quarantine",
            False,
        )
        group.add(self._quarantine_row)

        # Notifications
        self._notify_row = create_switch_row(icon_name="dialog-information-symbolic")
        self._notify_row.set_title(_("Notifications"))
        self._notify_row.set_subtitle(_("Show desktop notifications for device scan events"))
        self._notify_handler_id = self._notify_row.connect(
            "notify::active", self._on_notify_changed
        )
        self._load_switch(
            self._notify_row,
            self._notify_handler_id,
            "device_auto_scan_notify",
            True,
        )
        group.add(self._notify_row)

        # Skip on battery
        self._battery_row = create_switch_row(icon_name="battery-symbolic")
        self._battery_row.set_title(_("Skip on Battery"))
        self._battery_row.set_subtitle(_("Do not scan devices when running on battery power"))
        self._battery_handler_id = self._battery_row.connect(
            "notify::active", self._on_battery_changed
        )
        self._load_switch(
            self._battery_row,
            self._battery_handler_id,
            "device_auto_scan_skip_on_battery",
            True,
        )
        group.add(self._battery_row)

        return group

    # --- Auto-save handlers ---

    def _on_enable_changed(self, row, _pspec):
        """Handle enable toggle change."""
        if self._settings_manager:
            self._settings_manager.set("device_auto_scan_enabled", row.get_active())

    def _on_device_type_changed(self, _row, _pspec):
        """Handle device type toggle change - rebuild the types list."""
        if not self._settings_manager:
            return

        active_types = [
            type_key for type_key, (row, _handler_id) in self._type_rows.items() if row.get_active()
        ]
        self._settings_manager.set("device_auto_scan_types", active_types)

    def _on_max_size_changed(self, spin_button):
        """Handle max size spin change."""
        if self._settings_manager:
            self._settings_manager.set("device_auto_scan_max_size_gb", int(spin_button.get_value()))

    def _on_delay_changed(self, spin_button):
        """Handle delay spin change."""
        if self._settings_manager:
            self._settings_manager.set(
                "device_auto_scan_delay_seconds", int(spin_button.get_value())
            )

    def _on_quarantine_changed(self, row, _pspec):
        """Handle auto-quarantine toggle change."""
        if self._settings_manager:
            self._settings_manager.set("device_auto_scan_auto_quarantine", row.get_active())

    def _on_notify_changed(self, row, _pspec):
        """Handle notifications toggle change."""
        if self._settings_manager:
            self._settings_manager.set("device_auto_scan_notify", row.get_active())

    def _on_battery_changed(self, row, _pspec):
        """Handle skip-on-battery toggle change."""
        if self._settings_manager:
            self._settings_manager.set("device_auto_scan_skip_on_battery", row.get_active())

    # --- Helpers ---

    def _load_switch(self, row, handler_id, setting_key: str, default: bool):
        """Load a boolean setting into a switch row, blocking signal during load."""
        if self._settings_manager is None or row is None:
            return

        value = self._settings_manager.get(setting_key, default)

        if handler_id is not None:
            row.handler_block(handler_id)
        row.set_active(value)
        if handler_id is not None:
            row.handler_unblock(handler_id)
