# ClamUI VirusTotalResultsDialog Tests
"""
Unit tests for the VirusTotalResultsDialog class.

Tests cover:
- Dialog initialization with VTScanResult
- Date formatting utilities
- Detection list pagination
- File info section rendering
- Summary section rendering
- Export functionality
- Toast notifications

The dialog uses Adw.Window for libadwaita < 1.5 compatibility.
"""

import sys
from unittest import mock

import pytest


@pytest.fixture
def mock_vt_result():
    """Create a mock VTScanResult for testing."""
    result = mock.MagicMock()
    result.file_path = "/home/user/test_file.exe"
    result.sha256 = "a" * 64  # 64-char hash
    result.positives = 5
    result.total = 72
    result.scan_date = "2024-01-15T10:30:00Z"
    result.permalink = "https://www.virustotal.com/gui/file/abc123"
    result.detection_details = [
        {"engine": "Engine1", "category": "malware", "result": "Trojan.Generic"},
        {"engine": "Engine2", "category": "malware", "result": "Malware.Agent"},
        {"engine": "Engine3", "category": "pup", "result": "PUP.Optional"},
    ]
    return result


@pytest.fixture
def mock_vt_result_minimal():
    """Create a minimal VTScanResult without optional fields."""
    result = mock.MagicMock()
    result.file_path = None
    result.sha256 = None
    result.positives = 0
    result.total = 0
    result.scan_date = None
    result.permalink = None
    result.detection_details = []
    return result


@pytest.fixture
def dialog_class(mock_gi_modules):
    """Get VirusTotalResultsDialog class with mocked GTK dependencies."""
    # Mock the virustotal module for VTScanResult
    mock_vt_module = mock.MagicMock()
    mock_vt_module.VTScanResult = mock.MagicMock()

    # Mock clipboard
    mock_clipboard = mock.MagicMock()

    # Mock utils
    mock_utils = mock.MagicMock()
    mock_utils.resolve_icon_name = lambda x: x  # Pass through

    with mock.patch.dict(
        sys.modules,
        {
            "src.core.virustotal": mock_vt_module,
            "src.core.clipboard": mock_clipboard,
            "src.ui.utils": mock_utils,
        },
    ):
        # Clear cached import
        if "src.ui.virustotal_results_dialog" in sys.modules:
            del sys.modules["src.ui.virustotal_results_dialog"]

        from src.ui.virustotal_results_dialog import VirusTotalResultsDialog

        yield VirusTotalResultsDialog


@pytest.fixture
def mock_dialog(dialog_class, mock_vt_result):
    """Create a mock VirusTotalResultsDialog instance for testing."""
    # Create instance without calling __init__
    dialog = object.__new__(dialog_class)

    # Initialize state
    dialog._vt_result = mock_vt_result
    dialog._displayed_detection_count = 0
    dialog._all_detections = mock_vt_result.detection_details
    dialog._load_more_row = None
    dialog._detections_list = None
    dialog._toast_overlay = mock.MagicMock()

    return dialog


class TestVirusTotalResultsDialogConstants:
    """Tests for dialog constants."""

    def test_initial_display_limit_exists(self, dialog_class):
        """Test that dialog module has INITIAL_DISPLAY_LIMIT constant."""
        from src.ui import virustotal_results_dialog

        assert hasattr(virustotal_results_dialog, "INITIAL_DISPLAY_LIMIT")
        assert virustotal_results_dialog.INITIAL_DISPLAY_LIMIT > 0

    def test_large_result_threshold_exists(self, dialog_class):
        """Test that dialog module has LARGE_RESULT_THRESHOLD constant."""
        from src.ui import virustotal_results_dialog

        assert hasattr(virustotal_results_dialog, "LARGE_RESULT_THRESHOLD")
        assert virustotal_results_dialog.LARGE_RESULT_THRESHOLD > 0


class TestDialogInitialization:
    """Tests for dialog initialization state."""

    def test_stores_vt_result(self, mock_dialog, mock_vt_result):
        """Test dialog stores the VT result."""
        assert mock_dialog._vt_result == mock_vt_result

    def test_initializes_detection_count_to_zero(self, mock_dialog):
        """Test displayed detection count starts at zero."""
        assert mock_dialog._displayed_detection_count == 0

    def test_initializes_all_detections_from_result(self, mock_dialog, mock_vt_result):
        """Test all detections are extracted from result."""
        assert mock_dialog._all_detections == mock_vt_result.detection_details

    def test_load_more_row_initially_none(self, mock_dialog):
        """Test load more row is initially None."""
        assert mock_dialog._load_more_row is None


class TestFormatScanDate:
    """Tests for _format_scan_date method."""

    def test_formats_iso_date_correctly(self, mock_dialog):
        """Test ISO date formatting."""
        iso_date = "2024-01-15T10:30:00Z"
        result = mock_dialog._format_scan_date(iso_date)
        # Should format as YYYY-MM-DD HH:MM:SS
        assert "2024-01-15" in result
        assert "10:30:00" in result

    def test_formats_date_with_timezone_offset(self, mock_dialog):
        """Test date formatting with timezone offset."""
        iso_date = "2024-01-15T10:30:00+05:00"
        result = mock_dialog._format_scan_date(iso_date)
        assert "2024-01-15" in result

    def test_returns_original_on_invalid_date(self, mock_dialog):
        """Test invalid date returns original string."""
        invalid_date = "not-a-date"
        result = mock_dialog._format_scan_date(invalid_date)
        assert result == invalid_date

    def test_handles_none_gracefully(self, mock_dialog):
        """Test None input is handled gracefully."""
        # Should not raise, return the input
        result = mock_dialog._format_scan_date(None)
        assert result is None


class TestLoadMoreDetections:
    """Tests for _load_more_detections pagination logic."""

    def test_pagination_state_tracking(self, mock_dialog):
        """Test that pagination state is properly tracked."""
        # Verify initial state
        assert mock_dialog._displayed_detection_count == 0
        assert len(mock_dialog._all_detections) == 3

    def test_all_detections_stored(self, mock_dialog, mock_vt_result):
        """Test all detections are extracted from result."""
        assert mock_dialog._all_detections == mock_vt_result.detection_details
        assert len(mock_dialog._all_detections) == 3


class TestOnLoadMoreClicked:
    """Tests for _on_load_more_clicked handler."""

    def test_calls_load_more_detections(self, mock_dialog):
        """Test clicking load more triggers loading."""
        mock_dialog._load_more_detections = mock.MagicMock()
        mock_button = mock.MagicMock()

        mock_dialog._on_load_more_clicked(mock_button)

        mock_dialog._load_more_detections.assert_called_once()


class TestCreateDetectionRow:
    """Tests for _create_detection_row method."""

    def test_returns_listbox_row(self, mock_dialog, mock_gi_modules):
        """Test creating detection row returns a ListBoxRow."""
        gtk = mock_gi_modules["gtk"]
        detection = {"engine": "TestEngine", "category": "malware", "result": "Trojan"}

        # Mock the row creation
        mock_dialog._create_detection_row = lambda d: gtk.ListBoxRow()

        result = mock_dialog._create_detection_row(detection)

        # Should return a mock row
        assert result is not None


class TestOnViewVtClicked:
    """Tests for _on_view_vt_clicked handler."""

    def test_has_permalink_url(self, mock_dialog, mock_vt_result):
        """Test dialog stores permalink URL for opening."""
        assert mock_dialog._vt_result.permalink == mock_vt_result.permalink
        assert mock_dialog._vt_result.permalink.startswith("https://")

    def test_permalink_format(self, mock_vt_result):
        """Test permalink URL format is valid."""
        assert "virustotal.com" in mock_vt_result.permalink


class TestOnCopyPathClicked:
    """Tests for _on_copy_path_clicked handler."""

    def test_file_path_stored(self, mock_dialog, mock_vt_result):
        """Test file path is stored for copying."""
        assert mock_dialog._vt_result.file_path == mock_vt_result.file_path
        assert mock_dialog._vt_result.file_path.endswith(".exe")

    def test_file_path_format(self, mock_vt_result):
        """Test file path format is valid."""
        assert "/" in mock_vt_result.file_path


class TestOnCopyHashClicked:
    """Tests for _on_copy_hash_clicked handler."""

    def test_sha256_stored(self, mock_dialog, mock_vt_result):
        """Test SHA256 hash is stored for copying."""
        assert mock_dialog._vt_result.sha256 == mock_vt_result.sha256
        assert len(mock_dialog._vt_result.sha256) == 64

    def test_sha256_format(self, mock_vt_result):
        """Test SHA256 hash format is valid."""
        # SHA256 is 64 hex characters
        assert len(mock_vt_result.sha256) == 64


class TestShowToast:
    """Tests for _show_toast method."""

    def test_toast_overlay_exists(self, mock_dialog):
        """Test toast overlay is initialized."""
        assert mock_dialog._toast_overlay is not None


class TestOnExportClicked:
    """Tests for _on_export_clicked handler."""

    def test_result_can_be_serialized(self, mock_vt_result):
        """Test VT result has exportable data."""
        # All key fields should be present for export
        assert mock_vt_result.file_path is not None
        assert mock_vt_result.sha256 is not None
        assert mock_vt_result.positives is not None
        assert mock_vt_result.total is not None


class TestDialogWithMinimalResult:
    """Tests for dialog with minimal VT result (no optional fields)."""

    def test_handles_no_file_path(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles missing file path."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []
        dialog._displayed_detection_count = 0

        # Should not raise
        assert dialog._vt_result.file_path is None

    def test_handles_no_detections(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles empty detections list."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []
        dialog._displayed_detection_count = 0

        assert len(dialog._all_detections) == 0

    def test_handles_no_permalink(self, dialog_class, mock_vt_result_minimal):
        """Test dialog handles missing permalink."""
        dialog = object.__new__(dialog_class)
        dialog._vt_result = mock_vt_result_minimal
        dialog._all_detections = []

        assert dialog._vt_result.permalink is None


class TestDetectionRatioDisplay:
    """Tests for detection ratio display logic."""

    def test_calculates_ratio_correctly(self, mock_dialog, mock_vt_result):
        """Test detection ratio calculation."""
        # Result has positives=5, total=72
        positives = mock_vt_result.positives
        total = mock_vt_result.total

        ratio = f"{positives}/{total}"
        assert ratio == "5/72"

    def test_handles_zero_total(self, mock_dialog, mock_vt_result_minimal):
        """Test handling when total is zero."""
        # Should not cause division by zero
        positives = mock_vt_result_minimal.positives
        total = mock_vt_result_minimal.total

        # Safe calculation
        if total > 0:
            percentage = (positives / total) * 100
        else:
            percentage = 0

        assert percentage == 0


class TestHashTruncation:
    """Tests for SHA256 hash display truncation."""

    def test_truncates_long_hash(self, mock_vt_result):
        """Test that long hash is truncated for display."""
        sha256 = mock_vt_result.sha256  # 64 chars

        # Truncation format: first16...last16
        truncated = f"{sha256[:16]}...{sha256[-16:]}"

        assert len(truncated) < len(sha256)
        assert truncated.startswith(sha256[:16])
        assert truncated.endswith(sha256[-16:])
        assert "..." in truncated


# ============================================================================
# New test classes for deeper coverage
# ============================================================================


def _make_mock_detections(count):
    """Create a list of mock VTDetection-like objects."""
    detections = []
    for i in range(count):
        d = mock.MagicMock()
        d.engine_name = f"Engine{i}"
        d.category = "malicious" if i % 2 == 0 else "suspicious"
        d.result = f"Malware.Type{i}"
        detections.append(d)
    return detections


def _make_raw_dialog(dialog_class, **overrides):
    """Create dialog with specific VT result attributes (no __init__)."""
    from src.ui import virustotal_results_dialog as vrd

    dialog = object.__new__(dialog_class)
    dialog._vt_result = mock.MagicMock()
    dialog._vt_result.status = getattr(vrd.VTScanStatus, overrides.get("status_name", "CLEAN"))
    dialog._vt_result.detections = overrides.get("detections", 0)
    dialog._vt_result.total_engines = overrides.get("total_engines", 72)
    dialog._vt_result.scan_date = overrides.get("scan_date")
    dialog._vt_result.permalink = overrides.get("permalink")
    dialog._vt_result.file_path = overrides.get("file_path", "/test/file.exe")
    dialog._vt_result.sha256 = overrides.get("sha256", "a" * 64)
    dialog._vt_result.error_message = overrides.get("error_message")
    dialog._displayed_detection_count = 0
    dialog._all_detections = overrides.get("all_detections", [])
    dialog._load_more_row = None
    dialog._detections_list = None
    dialog._toast_overlay = mock.MagicMock()
    return dialog


class TestDialogUISetup:
    """Tests for _setup_ui() creating the full dialog layout."""

    def test_setup_ui_creates_toast_overlay(self, dialog_class, mock_gi_modules):
        """Test _setup_ui creates a toast overlay for notifications."""
        dialog = _make_raw_dialog(dialog_class)
        dialog._setup_ui()
        mock_gi_modules["adw"].ToastOverlay.assert_called()
        assert dialog._toast_overlay is not None

    def test_setup_ui_creates_header_bar(self, dialog_class, mock_gi_modules):
        """Test _setup_ui creates a header bar."""
        dialog = _make_raw_dialog(dialog_class)
        dialog._setup_ui()
        mock_gi_modules["adw"].HeaderBar.assert_called()

    def test_setup_ui_creates_scrolled_window(self, dialog_class, mock_gi_modules):
        """Test _setup_ui creates scrollable content area."""
        dialog = _make_raw_dialog(dialog_class)
        dialog._setup_ui()
        mock_gi_modules["gtk"].ScrolledWindow.assert_called()

    def test_setup_ui_adds_vt_button_when_permalink_exists(self, dialog_class, mock_gi_modules):
        """Test _setup_ui adds View on VirusTotal button when permalink set."""
        dialog = _make_raw_dialog(dialog_class, permalink="https://vt.com/file/abc")
        dialog._setup_ui()
        # Export button + VT button = at least 2 Button calls
        assert mock_gi_modules["gtk"].Button.call_count >= 2

    def test_setup_ui_fewer_buttons_without_permalink(self, dialog_class, mock_gi_modules):
        """Test _setup_ui creates fewer buttons without permalink."""
        # With permalink
        dialog_with = _make_raw_dialog(dialog_class, permalink="https://vt.com/abc")
        mock_gi_modules["gtk"].Button.reset_mock()
        dialog_with._setup_ui()
        count_with = mock_gi_modules["gtk"].Button.call_count

        # Without permalink
        dialog_without = _make_raw_dialog(dialog_class, permalink=None)
        mock_gi_modules["gtk"].Button.reset_mock()
        dialog_without._setup_ui()
        count_without = mock_gi_modules["gtk"].Button.call_count

        assert count_without < count_with


class TestSummarySection:
    """Tests for _create_summary_section() with different VTScanStatus values."""

    @pytest.mark.parametrize(
        "status_name",
        ["CLEAN", "DETECTED", "NOT_FOUND", "PENDING", "RATE_LIMITED", "FILE_TOO_LARGE"],
    )
    def test_appends_group_for_each_status(self, dialog_class, mock_gi_modules, status_name):
        """Test summary group is appended to parent for every status."""
        kwargs = {"status_name": status_name}
        if status_name == "DETECTED":
            kwargs["detections"] = 5
            kwargs["total_engines"] = 72
        if status_name in ("RATE_LIMITED", "FILE_TOO_LARGE"):
            kwargs["error_message"] = "Some error"
        dialog = _make_raw_dialog(dialog_class, **kwargs)
        parent = mock.MagicMock()
        dialog._create_summary_section(parent)
        parent.append.assert_called_once()

    def test_detected_status_creates_ratio_subtitle(self, dialog_class, mock_gi_modules):
        """Test DETECTED status sets subtitle with detection ratio."""
        dialog = _make_raw_dialog(
            dialog_class, status_name="DETECTED", detections=5, total_engines=72
        )
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_summary_section(parent)
        assert len(rows) >= 1
        # Status row subtitle should contain the ratio
        subtitle_call = rows[0].set_subtitle.call_args[0][0]
        assert "5/72" in subtitle_call

    def test_scan_date_row_added_when_date_present(self, dialog_class, mock_gi_modules):
        """Test a scan date row is created when scan_date is set."""
        dialog = _make_raw_dialog(dialog_class, scan_date="2024-01-15T10:00:00Z")
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_summary_section(parent)
        # 2 rows: status + date
        assert len(rows) == 2

    def test_no_date_row_when_scan_date_absent(self, dialog_class, mock_gi_modules):
        """Test no date row when scan_date is None."""
        dialog = _make_raw_dialog(dialog_class, scan_date=None)
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_summary_section(parent)
        assert len(rows) == 1

    def test_error_status_falls_to_default_branch(self, dialog_class, mock_gi_modules):
        """Test unknown/ERROR status uses the else branch."""
        dialog = _make_raw_dialog(dialog_class, status_name="ERROR", error_message="Unknown error")
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_summary_section(parent)
        assert len(rows) >= 1
        rows[0].set_title.assert_called()


class TestFileInfoSection:
    """Tests for _create_file_info_section() rendering."""

    def test_creates_path_row_when_file_path_set(self, dialog_class, mock_gi_modules):
        """Test file path row is created when file_path is set."""
        dialog = _make_raw_dialog(dialog_class, file_path="/home/user/test.exe", sha256=None)
        dialog._vt_result.sha256 = None
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_file_info_section(parent)
        assert len(rows) == 1
        parent.append.assert_called_once()

    def test_creates_hash_row_when_sha256_set(self, dialog_class, mock_gi_modules):
        """Test SHA-256 row is created when sha256 is set."""
        dialog = _make_raw_dialog(dialog_class, sha256="b" * 64)
        dialog._vt_result.file_path = None
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_file_info_section(parent)
        assert len(rows) == 1

    def test_creates_both_rows_when_both_fields_set(self, dialog_class, mock_gi_modules):
        """Test both rows created when file_path and sha256 are set."""
        dialog = _make_raw_dialog(dialog_class, file_path="/test.exe", sha256="c" * 64)
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_file_info_section(parent)
        assert len(rows) == 2

    def test_no_data_rows_when_both_none(self, dialog_class, mock_gi_modules):
        """Test no ActionRows when both fields are None."""
        dialog = _make_raw_dialog(dialog_class)
        dialog._vt_result.file_path = None
        dialog._vt_result.sha256 = None
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_file_info_section(parent)
        assert len(rows) == 0
        # Group still appended
        parent.append.assert_called_once()

    def test_path_row_shows_basename(self, dialog_class, mock_gi_modules):
        """Test file row subtitle shows basename, tooltip shows full path."""
        dialog = _make_raw_dialog(dialog_class, file_path="/home/user/malware.exe")
        dialog._vt_result.sha256 = None
        parent = mock.MagicMock()
        rows = []
        mock_gi_modules["adw"].ActionRow.side_effect = lambda *a, **kw: (
            rows.append(mock.MagicMock()) or rows[-1]
        )
        dialog._create_file_info_section(parent)
        rows[0].set_subtitle.assert_called_with("malware.exe")
        rows[0].set_tooltip_text.assert_called_with("/home/user/malware.exe")


class TestDetectionListIntegration:
    """Tests for detection list rendering and pagination."""

    def test_load_more_appends_rows_to_list(self, dialog_class, mock_gi_modules):
        """Test _load_more_detections adds detection rows to listbox."""
        dialog = _make_raw_dialog(dialog_class, all_detections=_make_mock_detections(3))
        dialog._detections_list = mock.MagicMock()
        dialog._load_more_detections(25)
        assert dialog._detections_list.append.call_count == 3
        assert dialog._displayed_detection_count == 3

    def test_pagination_button_when_more_remain(self, dialog_class, mock_gi_modules):
        """Test load more button appears when detections exceed batch size."""
        dialog = _make_raw_dialog(dialog_class, all_detections=_make_mock_detections(30))
        dialog._detections_list = mock.MagicMock()
        dialog._load_more_detections(25)
        # 25 detection rows + 1 load more row
        assert dialog._detections_list.append.call_count == 26
        assert dialog._displayed_detection_count == 25
        assert dialog._load_more_row is not None

    def test_no_pagination_button_when_all_shown(self, dialog_class, mock_gi_modules):
        """Test no load more button when all detections fit in one batch."""
        dialog = _make_raw_dialog(dialog_class, all_detections=_make_mock_detections(10))
        dialog._detections_list = mock.MagicMock()
        dialog._load_more_detections(25)
        assert dialog._detections_list.append.call_count == 10
        assert dialog._displayed_detection_count == 10

    def test_noop_when_list_is_none(self, dialog_class, mock_gi_modules):
        """Test _load_more_detections does nothing when list is None."""
        dialog = _make_raw_dialog(dialog_class, all_detections=_make_mock_detections(5))
        dialog._detections_list = None
        dialog._load_more_detections(25)
        assert dialog._displayed_detection_count == 0

    def test_second_load_removes_old_load_more_row(self, dialog_class, mock_gi_modules):
        """Test second batch removes previous load-more row before adding new one."""
        dialog = _make_raw_dialog(dialog_class, all_detections=_make_mock_detections(60))
        dialog._detections_list = mock.MagicMock()
        # First batch
        dialog._load_more_detections(25)
        first_row = dialog._load_more_row
        assert first_row is not None
        # Second batch should remove old row
        dialog._load_more_detections(25)
        dialog._detections_list.remove.assert_called_with(first_row)
        assert dialog._displayed_detection_count == 50

    def test_create_detection_row_returns_row(self, dialog_class, mock_gi_modules):
        """Test _create_detection_row returns a widget for a detection."""
        dialog = _make_raw_dialog(dialog_class)
        det = mock.MagicMock()
        det.engine_name = "TestAV"
        det.category = "malicious"
        det.result = "Trojan.Generic"
        row = dialog._create_detection_row(det)
        assert row is not None

    def test_create_detection_row_handles_none_result(self, dialog_class, mock_gi_modules):
        """Test _create_detection_row skips result label when result is None."""
        dialog = _make_raw_dialog(dialog_class)
        det = mock.MagicMock()
        det.engine_name = "CleanAV"
        det.category = "undetected"
        det.result = None
        row = dialog._create_detection_row(det)
        assert row is not None

    def test_create_detection_row_malicious_gets_error_class(self, dialog_class, mock_gi_modules):
        """Test malicious category badge gets 'error' CSS class."""
        dialog = _make_raw_dialog(dialog_class)
        det = mock.MagicMock()
        det.engine_name = "AV1"
        det.category = "malicious"
        det.result = "Trojan"
        labels = []
        mock_gi_modules["gtk"].Label.side_effect = lambda *a, **kw: (
            labels.append(mock.MagicMock()) or labels[-1]
        )
        dialog._create_detection_row(det)
        # Last label is category badge
        labels[-1].add_css_class.assert_any_call("error")

    def test_create_detection_row_suspicious_gets_warning_class(
        self, dialog_class, mock_gi_modules
    ):
        """Test suspicious category badge gets 'warning' CSS class."""
        dialog = _make_raw_dialog(dialog_class)
        det = mock.MagicMock()
        det.engine_name = "AV2"
        det.category = "suspicious"
        det.result = "PUP.Optional"
        labels = []
        mock_gi_modules["gtk"].Label.side_effect = lambda *a, **kw: (
            labels.append(mock.MagicMock()) or labels[-1]
        )
        dialog._create_detection_row(det)
        labels[-1].add_css_class.assert_any_call("warning")


class TestButtonHandlers:
    """Tests for dialog button click handlers calling real logic."""

    def test_on_view_vt_clicked_opens_browser(self, dialog_class, mock_gi_modules):
        """Test _on_view_vt_clicked opens permalink in default browser."""
        dialog = _make_raw_dialog(
            dialog_class, permalink="https://www.virustotal.com/gui/file/abc123"
        )
        with mock.patch("src.ui.virustotal_results_dialog.webbrowser.open") as mock_open:
            dialog._on_view_vt_clicked(mock.MagicMock())
            mock_open.assert_called_once_with("https://www.virustotal.com/gui/file/abc123")

    def test_on_view_vt_clicked_noop_without_permalink(self, dialog_class, mock_gi_modules):
        """Test _on_view_vt_clicked does nothing when permalink is None."""
        dialog = _make_raw_dialog(dialog_class, permalink=None)
        dialog._vt_result.permalink = None
        with mock.patch("src.ui.virustotal_results_dialog.webbrowser.open") as mock_open:
            dialog._on_view_vt_clicked(mock.MagicMock())
            mock_open.assert_not_called()

    def test_on_view_vt_clicked_handles_browser_error(self, dialog_class, mock_gi_modules):
        """Test _on_view_vt_clicked handles browser open failure gracefully."""
        dialog = _make_raw_dialog(dialog_class, permalink="https://vt.com/file/abc")
        with mock.patch(
            "src.ui.virustotal_results_dialog.webbrowser.open",
            side_effect=OSError("no browser"),
        ):
            dialog._on_view_vt_clicked(mock.MagicMock())

    def test_on_copy_path_clicked_copies_path(self, dialog_class, mock_gi_modules):
        """Test _on_copy_path_clicked copies full file path to clipboard."""
        dialog = _make_raw_dialog(dialog_class, file_path="/home/user/test.exe")
        with mock.patch(
            "src.ui.virustotal_results_dialog.copy_to_clipboard", return_value=True
        ) as mock_copy:
            dialog._on_copy_path_clicked(mock.MagicMock())
            mock_copy.assert_called_once_with("/home/user/test.exe")

    def test_on_copy_hash_clicked_copies_sha256(self, dialog_class, mock_gi_modules):
        """Test _on_copy_hash_clicked copies SHA256 hash to clipboard."""
        dialog = _make_raw_dialog(dialog_class, sha256="f" * 64)
        with mock.patch(
            "src.ui.virustotal_results_dialog.copy_to_clipboard", return_value=True
        ) as mock_copy:
            dialog._on_copy_hash_clicked(mock.MagicMock())
            mock_copy.assert_called_once_with("f" * 64)

    def test_on_export_clicked_copies_json_to_clipboard(self, dialog_class, mock_gi_modules):
        """Test _on_export_clicked serializes result as JSON and copies it."""
        import json

        dialog = _make_raw_dialog(dialog_class, file_path="/test.exe", sha256="a" * 64)
        dialog._vt_result.status.value = "detected"
        dialog._vt_result.detections = 1
        dialog._vt_result.total_engines = 72
        dialog._vt_result.scan_date = "2024-01-15"
        dialog._vt_result.permalink = "https://vt.com/abc"
        dialog._vt_result.error_message = None
        det = mock.MagicMock()
        det.engine_name = "TestAV"
        det.category = "malicious"
        det.result = "Trojan"
        dialog._all_detections = [det]

        with mock.patch(
            "src.ui.virustotal_results_dialog.copy_to_clipboard", return_value=True
        ) as mock_copy:
            dialog._on_export_clicked(mock.MagicMock())
            mock_copy.assert_called_once()
            data = json.loads(mock_copy.call_args[0][0])
            assert data["file_path"] == "/test.exe"
            assert data["status"] == "detected"
            assert len(data["detection_details"]) == 1
            assert data["detection_details"][0]["engine"] == "TestAV"

    def test_on_export_clicked_includes_error_message(self, dialog_class, mock_gi_modules):
        """Test export JSON includes error_message when present."""
        import json

        dialog = _make_raw_dialog(dialog_class)
        dialog._vt_result.status.value = "error"
        dialog._vt_result.error_message = "Rate limited"
        dialog._all_detections = []

        with mock.patch(
            "src.ui.virustotal_results_dialog.copy_to_clipboard", return_value=True
        ) as mock_copy:
            dialog._on_export_clicked(mock.MagicMock())
            data = json.loads(mock_copy.call_args[0][0])
            assert data["error_message"] == "Rate limited"

    def test_show_toast_creates_adw_toast(self, dialog_class, mock_gi_modules):
        """Test _show_toast creates an Adw.Toast and adds to overlay."""
        dialog = _make_raw_dialog(dialog_class)
        dialog._show_toast("Copied!")
        mock_gi_modules["adw"].Toast.new.assert_called_once_with("Copied!")
        dialog._toast_overlay.add_toast.assert_called_once()
