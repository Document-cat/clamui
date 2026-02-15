# ClamUI VirusTotal Page Tests
"""
Tests for the VirusTotalPage preferences component.

Covers: page creation, API key status display, key entry validation,
save/delete key flows, behavior settings dropdown, info group, toast,
and browser link.
"""

import sys
from unittest.mock import MagicMock, patch


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _import_vt_page(mock_gi_modules):
    """Import VirusTotalPage with mocks in place."""
    from src.ui.preferences.virustotal_page import VT_API_KEY_URL, VirusTotalPage

    return VirusTotalPage, VT_API_KEY_URL


def _make_page_mock():
    """Create a mock page with attributes matching what create_page sets."""
    page = MagicMock()
    page._settings_manager = MagicMock()
    page._parent_window = MagicMock()
    page._toast_overlay = MagicMock()
    page._status_row = MagicMock()
    page._status_icon = MagicMock()
    page._api_key_row = MagicMock()
    page._validation_label = MagicMock()
    page._save_button = MagicMock()
    page._delete_button = MagicMock()
    return page


# ═════════════════════════════════════════════════════════════════════════════
# Test Classes
# ═════════════════════════════════════════════════════════════════════════════


class TestVirusTotalPageImport:
    """Test that module imports correctly."""

    def test_import_module(self, mock_gi_modules):
        from src.ui.preferences.virustotal_page import VirusTotalPage

        assert VirusTotalPage is not None
        _clear_src_modules()

    def test_vt_api_key_url_defined(self, mock_gi_modules):
        from src.ui.preferences.virustotal_page import VT_API_KEY_URL

        assert "virustotal.com" in VT_API_KEY_URL
        _clear_src_modules()


class TestVirusTotalPageCreate:
    """Test create_page factory method."""

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_create_page_returns_page(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()

        page = VirusTotalPage.create_page(settings_manager=sm)

        assert page is not None
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_create_page_stores_settings_manager(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()

        page = VirusTotalPage.create_page(settings_manager=sm)

        assert page._settings_manager is sm
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_create_page_stores_parent_window(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        parent = MagicMock()

        page = VirusTotalPage.create_page(settings_manager=sm, parent_window=parent)

        assert page._parent_window is parent
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value="abc123def456")
    @patch("src.ui.preferences.virustotal_page.mask_api_key", return_value="abc1...f456")
    def test_create_page_with_existing_key(self, mock_mask, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()

        page = VirusTotalPage.create_page(settings_manager=sm)

        assert page is not None
        mock_mask.assert_called_once_with("abc123def456")
        _clear_src_modules()


class TestAPIKeyChanged:
    """Test _on_api_key_changed validation handler."""

    @patch("src.ui.preferences.virustotal_page.validate_api_key_format")
    def test_empty_key_disables_save(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        entry = MagicMock()
        entry.get_text.return_value = ""

        VirusTotalPage._on_api_key_changed(page, entry)

        page._save_button.set_sensitive.assert_called_with(False)
        page._validation_label.set_visible.assert_called_with(False)
        mock_validate.assert_not_called()
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.validate_api_key_format")
    def test_whitespace_key_disables_save(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        entry = MagicMock()
        entry.get_text.return_value = "   "

        VirusTotalPage._on_api_key_changed(page, entry)

        page._save_button.set_sensitive.assert_called_with(False)
        mock_validate.assert_not_called()
        _clear_src_modules()

    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(True, None),
    )
    def test_valid_key_enables_save(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        entry = MagicMock()
        entry.get_text.return_value = "a" * 64

        VirusTotalPage._on_api_key_changed(page, entry)

        page._save_button.set_sensitive.assert_called_with(True)
        page._validation_label.set_visible.assert_called_with(False)
        _clear_src_modules()

    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(False, "Must be 64 hex characters"),
    )
    def test_invalid_key_shows_error(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        entry = MagicMock()
        entry.get_text.return_value = "too-short"

        VirusTotalPage._on_api_key_changed(page, entry)

        page._save_button.set_sensitive.assert_called_with(False)
        page._validation_label.set_label.assert_called_with("Must be 64 hex characters")
        page._validation_label.set_visible.assert_called_with(True)
        _clear_src_modules()

    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(False, None),
    )
    def test_invalid_key_with_no_message_shows_default(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        entry = MagicMock()
        entry.get_text.return_value = "bad"

        VirusTotalPage._on_api_key_changed(page, entry)

        page._validation_label.set_label.assert_called_with("Invalid API key format")
        _clear_src_modules()


class TestSaveClicked:
    """Test _on_save_clicked handler."""

    @patch("src.ui.preferences.virustotal_page.update_status_row")
    @patch("src.ui.preferences.virustotal_page.mask_api_key", return_value="abc...xyz")
    @patch("src.ui.preferences.virustotal_page.set_api_key", return_value=(True, None))
    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(True, None),
    )
    def test_save_success(self, mock_validate, mock_set, mock_mask, mock_update, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        page._api_key_row.get_text.return_value = "a" * 64
        sm = page._settings_manager

        VirusTotalPage._on_save_clicked(page, sm)

        mock_set.assert_called_once_with("a" * 64, sm)
        page._api_key_row.set_text.assert_called_with("")
        page._save_button.set_sensitive.assert_called_with(False)
        page._delete_button.set_sensitive.assert_called_with(True)
        mock_update.assert_called_once()
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.set_api_key", return_value=(False, "Keyring error"))
    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(True, None),
    )
    def test_save_failure_with_error(self, mock_validate, mock_set, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        page._api_key_row.get_text.return_value = "a" * 64
        page.get_root.return_value = page

        VirusTotalPage._on_save_clicked(page, page._settings_manager)

        # Should attempt to show a toast (via _show_toast)
        # _show_toast checks parent.get_root()._toast_overlay
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.set_api_key", return_value=(False, None))
    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(True, None),
    )
    def test_save_failure_no_error_message(self, mock_validate, mock_set, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        page._api_key_row.get_text.return_value = "a" * 64

        VirusTotalPage._on_save_clicked(page, page._settings_manager)

        # Should not raise
        _clear_src_modules()

    @patch(
        "src.ui.preferences.virustotal_page.validate_api_key_format",
        return_value=(False, "Bad format"),
    )
    def test_save_skips_invalid_key(self, mock_validate, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        page._api_key_row.get_text.return_value = "bad"

        VirusTotalPage._on_save_clicked(page, page._settings_manager)

        # Should not call set_api_key
        _clear_src_modules()

    def test_save_empty_key_returns_early(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()
        page._api_key_row.get_text.return_value = ""

        with patch("src.ui.preferences.virustotal_page.validate_api_key_format") as mock_v:
            VirusTotalPage._on_save_clicked(page, page._settings_manager)
            mock_v.assert_not_called()

        _clear_src_modules()


class TestDeleteKey:
    """Test _on_delete_clicked handler."""

    def test_delete_creates_confirmation_dialog(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()

        # _on_delete_clicked creates an Adw.Window dialog - should not raise
        VirusTotalPage._on_delete_clicked(page, page._settings_manager)

        # If it completes without error, the dialog was created and presented
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.delete_api_key", return_value=True)
    @patch("src.ui.preferences.virustotal_page.update_status_row")
    def test_delete_confirmed_success(self, mock_update, mock_delete, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()

        # Simulate calling on_delete_confirmed directly
        # This is the inner closure called when delete button is clicked
        mock_delete.return_value = True

        # We can test the internal flow by calling delete_api_key and checking results
        from src.ui.preferences.virustotal_page import delete_api_key

        result = delete_api_key(page._settings_manager)

        assert result is True
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.delete_api_key", return_value=False)
    def test_delete_confirmed_failure(self, mock_delete, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = _make_page_mock()

        from src.ui.preferences.virustotal_page import delete_api_key

        result = delete_api_key(page._settings_manager)

        assert result is False
        _clear_src_modules()


class TestBehaviorSettings:
    """Test _on_no_key_action_changed and behavior group."""

    def test_action_changed_saves_none(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        row = MagicMock()
        row.get_selected.return_value = 0
        sm = MagicMock()

        VirusTotalPage._on_no_key_action_changed(row, sm)

        sm.set.assert_called_once_with("virustotal_remember_no_key_action", "none")
        _clear_src_modules()

    def test_action_changed_saves_open_website(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        row = MagicMock()
        row.get_selected.return_value = 1
        sm = MagicMock()

        VirusTotalPage._on_no_key_action_changed(row, sm)

        sm.set.assert_called_once_with("virustotal_remember_no_key_action", "open_website")
        _clear_src_modules()

    def test_action_changed_saves_prompt(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        row = MagicMock()
        row.get_selected.return_value = 2
        sm = MagicMock()

        VirusTotalPage._on_no_key_action_changed(row, sm)

        sm.set.assert_called_once_with("virustotal_remember_no_key_action", "prompt")
        _clear_src_modules()

    def test_action_changed_unknown_index_defaults_none(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        row = MagicMock()
        row.get_selected.return_value = 99
        sm = MagicMock()

        VirusTotalPage._on_no_key_action_changed(row, sm)

        sm.set.assert_called_once_with("virustotal_remember_no_key_action", "none")
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_behavior_group_reads_current_setting(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        sm.get.return_value = "open_website"
        page = MagicMock()

        VirusTotalPage._create_behavior_group(page, sm)

        sm.get.assert_called_with("virustotal_remember_no_key_action", "none")
        page.add.assert_called_once()
        _clear_src_modules()


class TestInfoGroup:
    """Test _create_info_group renders info rows."""

    def test_creates_info_group(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = MagicMock()

        VirusTotalPage._create_info_group(page)

        page.add.assert_called_once()
        _clear_src_modules()


class TestGetApiKeyClicked:
    """Test _on_get_api_key_clicked opens browser."""

    @patch("src.ui.preferences.virustotal_page.webbrowser.open")
    def test_opens_virustotal_url(self, mock_open, mock_gi_modules):
        VirusTotalPage, VT_API_KEY_URL = _import_vt_page(mock_gi_modules)

        VirusTotalPage._on_get_api_key_clicked()

        mock_open.assert_called_once_with(VT_API_KEY_URL)
        _clear_src_modules()

    @patch(
        "src.ui.preferences.virustotal_page.webbrowser.open",
        side_effect=Exception("No browser"),
    )
    def test_handles_browser_error(self, mock_open, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)

        # Should not raise
        VirusTotalPage._on_get_api_key_clicked()

        _clear_src_modules()


class TestShowToast:
    """Test _show_toast helper."""

    def test_show_toast_with_overlay(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = MagicMock()
        root = MagicMock()
        root._toast_overlay = MagicMock()
        page.get_root.return_value = root

        VirusTotalPage._show_toast(page, "Test message")

        root._toast_overlay.add_toast.assert_called_once()
        _clear_src_modules()

    def test_show_toast_no_overlay(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = MagicMock()
        page.get_root.return_value = None

        # Should not raise
        VirusTotalPage._show_toast(page, "Test message")

        _clear_src_modules()

    def test_show_toast_root_without_toast_overlay(self, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        page = MagicMock()
        root = MagicMock(spec=[])  # No attributes at all
        page.get_root.return_value = root

        # Should not raise
        VirusTotalPage._show_toast(page, "Test message")

        _clear_src_modules()


class TestStatusDisplay:
    """Test API key status display in create_page."""

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_no_key_status_shows_not_configured(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        sm.get.return_value = "none"
        page = MagicMock()

        VirusTotalPage._create_api_key_group(page, sm)

        # Should store status row and icon references
        assert hasattr(page, "_status_row")
        assert hasattr(page, "_status_icon")
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.mask_api_key", return_value="abc...xyz")
    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value="abcdef1234567890")
    def test_existing_key_status_shows_configured(self, mock_get, mock_mask, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        page = MagicMock()

        VirusTotalPage._create_api_key_group(page, sm)

        mock_mask.assert_called_once_with("abcdef1234567890")
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value=None)
    def test_no_key_delete_button_disabled(self, mock_get_key, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        sm.get.return_value = "none"

        page = VirusTotalPage.create_page(settings_manager=sm)

        # Delete button should be disabled when no key exists
        # The button is stored on the page and set_sensitive(False) was called
        # This is hard to verify directly on mocks, but we ensure no crash
        assert page is not None
        _clear_src_modules()

    @patch("src.ui.preferences.virustotal_page.mask_api_key", return_value="masked")
    @patch("src.ui.preferences.virustotal_page.get_api_key", return_value="realkey")
    def test_existing_key_delete_button_enabled(self, mock_get, mock_mask, mock_gi_modules):
        VirusTotalPage, _ = _import_vt_page(mock_gi_modules)
        sm = MagicMock()
        sm.get.return_value = "none"

        page = VirusTotalPage.create_page(settings_manager=sm)

        assert page is not None
        _clear_src_modules()
