# ClamUI View Helpers Tests
"""
Unit tests for the view_helpers module.

Tests cover:
- StatusLevel enum values
- set_status_class() function
- clear_status_classes() function
- INFO status level (new for update view)
"""

import sys
from unittest import mock

import pytest


def _clear_src_modules():
    """Clear all cached src.* modules to prevent test pollution."""
    modules_to_remove = [mod for mod in sys.modules if mod.startswith("src.")]
    for mod in modules_to_remove:
        del sys.modules[mod]


@pytest.fixture
def view_helpers_module(mock_gi_modules):
    """Import view_helpers module with mocked GTK dependencies."""
    # Clear any cached import of view_helpers module
    if "src.ui.view_helpers" in sys.modules:
        del sys.modules["src.ui.view_helpers"]

    from src.ui import view_helpers

    yield view_helpers

    # Critical: Clear all src.* modules after test to prevent pollution
    _clear_src_modules()


@pytest.fixture
def mock_widget(mock_gi_modules):
    """Create a mock GTK widget."""
    widget = mock.MagicMock()
    widget.get_css_classes.return_value = []
    return widget


# =============================================================================
# StatusLevel Enum Tests
# =============================================================================


class TestStatusLevelEnum:
    """Tests for the StatusLevel enum."""

    def test_all_status_levels_defined(self, view_helpers_module):
        """Verify all expected status levels are defined."""
        StatusLevel = view_helpers_module.StatusLevel
        assert hasattr(StatusLevel, "SUCCESS")
        assert hasattr(StatusLevel, "WARNING")
        assert hasattr(StatusLevel, "ERROR")
        assert hasattr(StatusLevel, "INFO")

    def test_status_values(self, view_helpers_module):
        """Verify status string values."""
        StatusLevel = view_helpers_module.StatusLevel
        assert StatusLevel.SUCCESS.value == "success"
        assert StatusLevel.WARNING.value == "warning"
        assert StatusLevel.ERROR.value == "error"
        assert StatusLevel.INFO.value == "info"

    def test_status_count(self, view_helpers_module):
        """Verify exactly 4 status levels defined."""
        StatusLevel = view_helpers_module.StatusLevel
        assert len(StatusLevel) == 4


# =============================================================================
# set_status_class() Tests
# =============================================================================


class TestSetStatusClass:
    """Tests for the set_status_class() function."""

    def test_sets_success_class(self, view_helpers_module, mock_widget):
        """Test set_status_class sets success CSS class."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.SUCCESS)

        mock_widget.add_css_class.assert_called_once_with("success")
        # Should also remove other status classes
        assert mock_widget.remove_css_class.call_count >= 2

    def test_sets_warning_class(self, view_helpers_module, mock_widget):
        """Test set_status_class sets warning CSS class."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.WARNING)

        mock_widget.add_css_class.assert_called_once_with("warning")

    def test_sets_error_class(self, view_helpers_module, mock_widget):
        """Test set_status_class sets error CSS class."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.ERROR)

        mock_widget.add_css_class.assert_called_once_with("error")

    def test_sets_info_class(self, view_helpers_module, mock_widget):
        """Test set_status_class sets info CSS class."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.INFO)

        mock_widget.add_css_class.assert_called_once_with("info")

    def test_removes_other_status_classes(self, view_helpers_module, mock_widget):
        """Test set_status_class removes other status classes."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.INFO)

        # Should remove all other status classes
        remove_calls = [call[0][0] for call in mock_widget.remove_css_class.call_args_list]
        assert "success" in remove_calls
        assert "warning" in remove_calls
        assert "error" in remove_calls

    def test_does_not_remove_target_class(self, view_helpers_module, mock_widget):
        """Test set_status_class doesn't remove the class being set."""
        set_status_class = view_helpers_module.set_status_class
        StatusLevel = view_helpers_module.StatusLevel

        set_status_class(mock_widget, StatusLevel.SUCCESS)

        # Should not remove 'success' class
        for call in mock_widget.remove_css_class.call_args_list:
            assert call[0][0] != "success"


# =============================================================================
# clear_status_classes() Tests
# =============================================================================


class TestClearStatusClasses:
    """Tests for the clear_status_classes() function."""

    def test_clears_all_status_classes(self, view_helpers_module, mock_widget):
        """Test clear_status_classes removes all status classes."""
        clear_status_classes = view_helpers_module.clear_status_classes

        clear_status_classes(mock_widget)

        # Should remove all 4 status classes
        assert mock_widget.remove_css_class.call_count == 4
        remove_calls = [call[0][0] for call in mock_widget.remove_css_class.call_args_list]
        assert "success" in remove_calls
        assert "warning" in remove_calls
        assert "error" in remove_calls
        assert "info" in remove_calls


# =============================================================================
# create_empty_state() Tests
# =============================================================================


class TestCreateEmptyState:
    """Tests for the create_empty_state() function."""

    def test_creates_basic_empty_state(self, view_helpers_module):
        """Test create_empty_state creates a basic empty state widget."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
        )

        widget = create_empty_state(config)

        # Verify widget was created
        assert widget is not None
        # Verify append was called twice (icon + title)
        assert widget.append.call_count == 2

    def test_with_subtitle(self, view_helpers_module):
        """Test create_empty_state with subtitle."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            subtitle="Logs from scans will appear here",
        )

        widget = create_empty_state(config)

        # Should have 3 children: icon, title, subtitle
        assert widget.append.call_count == 3

    def test_with_custom_icon_size(self, view_helpers_module):
        """Test create_empty_state with custom icon size sets pixel size."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig
        Gtk = view_helpers_module.Gtk

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            icon_size=64,
        )

        create_empty_state(config)

        # Verify the image got the custom pixel size
        Gtk.Image.return_value.set_pixel_size.assert_called_with(64)

    def test_with_custom_margins(self, view_helpers_module):
        """Test create_empty_state with custom margins sets margin values."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            margin_vertical=36,
        )

        widget = create_empty_state(config)

        # Verify custom margins were applied to the box
        widget.set_margin_top.assert_called_with(36)
        widget.set_margin_bottom.assert_called_with(36)

    def test_with_title_css_class(self, view_helpers_module):
        """Test create_empty_state with title CSS class creates extra label styling."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig
        Gtk = view_helpers_module.Gtk

        # Track label mocks created via side_effect
        label_mocks = []
        original_side_effect = Gtk.Label.side_effect
        Gtk.Label.side_effect = lambda *a, **k: (
            label_mocks.append(mock.MagicMock()) or label_mocks[-1]
        )

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            title_css_class="heading",
        )

        create_empty_state(config)

        # Title label (first one) should have "heading" CSS class added
        assert len(label_mocks) >= 1
        title_label = label_mocks[0]
        css_calls = [c[0][0] for c in title_label.add_css_class.call_args_list]
        assert "heading" in css_calls

        Gtk.Label.side_effect = original_side_effect

    def test_center_horizontally(self, view_helpers_module):
        """Test create_empty_state with horizontal centering sets halign."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig
        Gtk = view_helpers_module.Gtk

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            center_horizontally=True,
        )

        widget = create_empty_state(config)

        # Verify horizontal alignment was set on the box
        widget.set_halign.assert_called_with(Gtk.Align.CENTER)

    def test_wrap_subtitle(self, view_helpers_module):
        """Test create_empty_state with subtitle wrapping calls set_wrap."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig
        Gtk = view_helpers_module.Gtk

        # Track label mocks to verify subtitle wrapping
        label_mocks = []
        Gtk.Label.side_effect = lambda *a, **k: (
            label_mocks.append(mock.MagicMock()) or label_mocks[-1]
        )

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            subtitle="This is a very long subtitle that should be wrapped",
            wrap_subtitle=True,
        )

        create_empty_state(config)

        # Subtitle label (second one) should have set_wrap(True)
        assert len(label_mocks) == 2
        subtitle_label = label_mocks[1]
        subtitle_label.set_wrap.assert_called_with(True)

    def test_max_subtitle_chars(self, view_helpers_module):
        """Test create_empty_state with max subtitle chars calls set_max_width_chars."""
        create_empty_state = view_helpers_module.create_empty_state
        EmptyStateConfig = view_helpers_module.EmptyStateConfig
        Gtk = view_helpers_module.Gtk

        # Track label mocks to verify max width chars
        label_mocks = []
        Gtk.Label.side_effect = lambda *a, **k: (
            label_mocks.append(mock.MagicMock()) or label_mocks[-1]
        )

        config = EmptyStateConfig(
            icon_name="document-open-recent-symbolic",
            title="No logs yet",
            subtitle="Short subtitle",
            max_subtitle_chars=50,
        )

        create_empty_state(config)

        # Subtitle label should have max width chars and center justification
        assert len(label_mocks) == 2
        subtitle_label = label_mocks[1]
        subtitle_label.set_max_width_chars.assert_called_with(50)
        subtitle_label.set_justify.assert_called_once()


# =============================================================================
# create_loading_row() Tests
# =============================================================================


class TestCreateLoadingRow:
    """Tests for the create_loading_row() function."""

    def test_creates_loading_row(self, view_helpers_module):
        """Test create_loading_row creates a non-selectable, non-activatable row."""
        create_loading_row = view_helpers_module.create_loading_row

        row = create_loading_row("Loading...")

        # Verify row is non-interactive
        row.set_selectable.assert_called_once_with(False)
        row.set_activatable.assert_called_once_with(False)
        # Verify a child widget was set on the row
        row.set_child.assert_called_once()

    def test_custom_margin_vertical(self, view_helpers_module):
        """Test create_loading_row with custom margin applies it to the box."""
        create_loading_row = view_helpers_module.create_loading_row

        row = create_loading_row("Loading...", margin_vertical=36)

        # The loading box inside the row should have custom margins
        # We verify via the row's set_child call - the box passed to it
        child_box = row.set_child.call_args[0][0]
        child_box.set_margin_top.assert_called_with(36)
        child_box.set_margin_bottom.assert_called_with(36)

    def test_row_not_selectable(self, view_helpers_module):
        """Test create_loading_row creates non-selectable row."""
        create_loading_row = view_helpers_module.create_loading_row

        row = create_loading_row("Loading...")

        # Row created with set_selectable(False) called
        row.set_selectable.assert_called_once_with(False)

    def test_row_not_activatable(self, view_helpers_module):
        """Test create_loading_row creates non-activatable row."""
        create_loading_row = view_helpers_module.create_loading_row

        row = create_loading_row("Loading...")

        # Row created with set_activatable(False) called
        row.set_activatable.assert_called_once_with(False)

    def test_spinner_spinning(self, view_helpers_module):
        """Test create_loading_row sets spinner to spinning."""
        create_loading_row = view_helpers_module.create_loading_row
        Gtk = view_helpers_module.Gtk

        create_loading_row("Loading...")

        # Verify the spinner was set to spinning
        Gtk.Spinner.return_value.set_spinning.assert_called_with(True)


# =============================================================================
# LoadingStateController Tests
# =============================================================================


class TestLoadingStateController:
    """Tests for the LoadingStateController class."""

    @pytest.fixture
    def mock_spinner(self):
        """Create a mock spinner widget."""
        spinner = mock.MagicMock()
        return spinner

    @pytest.fixture
    def mock_buttons(self):
        """Create mock buttons."""
        return [mock.MagicMock() for _ in range(2)]

    @pytest.fixture
    def mock_extra_buttons(self):
        """Create mock extra buttons."""
        return [mock.MagicMock() for _ in range(2)]

    def test_set_loading_true_shows_spinner(self, view_helpers_module):
        """Test set_loading(True) shows and starts spinner."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_button = mock.MagicMock()

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=[mock_button],
        )

        controller.set_loading(True)

        mock_spinner.set_visible.assert_called_once_with(True)
        mock_spinner.start.assert_called_once()

    def test_set_loading_true_disables_buttons(self, view_helpers_module):
        """Test set_loading(True) disables buttons."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_buttons = [mock.MagicMock(), mock.MagicMock()]

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=mock_buttons,
        )

        controller.set_loading(True)

        for button in mock_buttons:
            button.set_sensitive.assert_called_with(False)

    def test_set_loading_false_hides_spinner(self, view_helpers_module):
        """Test set_loading(False) hides and stops spinner."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_button = mock.MagicMock()

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=[mock_button],
        )

        controller.set_loading(False)

        mock_spinner.stop.assert_called_once()
        mock_spinner.set_visible.assert_called_with(False)

    def test_set_loading_false_enables_buttons(self, view_helpers_module):
        """Test set_loading(False) enables buttons."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_buttons = [mock.MagicMock(), mock.MagicMock()]

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=mock_buttons,
        )

        controller.set_loading(False)

        for button in mock_buttons:
            button.set_sensitive.assert_called_with(True)

    def test_with_extra_buttons(self, view_helpers_module):
        """Test LoadingStateController with extra buttons."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_buttons = [mock.MagicMock()]
        mock_extra_buttons = [mock.MagicMock(), mock.MagicMock()]

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=mock_buttons,
            extra_buttons=mock_extra_buttons,
        )

        controller.set_loading(True)

        # All buttons should be disabled
        mock_buttons[0].set_sensitive.assert_called_with(False)
        mock_extra_buttons[0].set_sensitive.assert_called_with(False)
        mock_extra_buttons[1].set_sensitive.assert_called_with(False)

    def test_without_extra_buttons(self, view_helpers_module):
        """Test LoadingStateController without extra buttons."""
        LoadingStateController = view_helpers_module.LoadingStateController

        mock_spinner = mock.MagicMock()
        mock_button = mock.MagicMock()

        controller = LoadingStateController(
            spinner=mock_spinner,
            buttons=[mock_button],
            extra_buttons=None,
        )

        controller.set_loading(True)

        # Should not crash, only main button disabled
        mock_button.set_sensitive.assert_called_with(False)


# =============================================================================
# create_header_button_box() Tests
# =============================================================================


class TestCreateHeaderButtonBox:
    """Tests for the create_header_button_box() function."""

    def test_creates_basic_button_box(self, view_helpers_module):
        """Test create_header_button_box creates a box."""
        create_header_button_box = view_helpers_module.create_header_button_box

        box, spinner = create_header_button_box(buttons=[])

        # Verify box was created and no spinner
        assert box is not None
        assert spinner is None

    def test_with_multiple_buttons(self, view_helpers_module):
        """Test create_header_button_box with multiple buttons."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton

        buttons = [
            HeaderButton(icon_name="view-refresh-symbolic"),
            HeaderButton(icon_name="edit-clear-all-symbolic"),
        ]

        box, spinner = create_header_button_box(buttons=buttons)

        # Verify box created and buttons appended
        assert box is not None
        assert box.append.call_count == 2

    def test_with_icon_name(self, view_helpers_module):
        """Test button with icon_name calls set_icon_name."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        buttons = [HeaderButton(icon_name="view-refresh-symbolic")]

        create_header_button_box(buttons=buttons)

        # Verify set_icon_name was called on the created button
        Gtk.Button.return_value.set_icon_name.assert_called_once()

    def test_with_label(self, view_helpers_module):
        """Test button with label calls set_label."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        buttons = [HeaderButton(label="Refresh")]

        create_header_button_box(buttons=buttons)

        # Verify set_label was called on the created button
        Gtk.Button.return_value.set_label.assert_called_once_with("Refresh")

    def test_with_tooltip(self, view_helpers_module):
        """Test button with tooltip calls set_tooltip_text."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        buttons = [HeaderButton(icon_name="view-refresh-symbolic", tooltip="Refresh data")]

        create_header_button_box(buttons=buttons)

        # Verify tooltip was set on the button
        Gtk.Button.return_value.set_tooltip_text.assert_called_once_with("Refresh data")

    def test_with_css_classes(self, view_helpers_module):
        """Test button with CSS classes adds them."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        buttons = [
            HeaderButton(icon_name="view-refresh-symbolic", css_classes=["suggested-action"])
        ]

        create_header_button_box(buttons=buttons)

        # Verify CSS classes were added (flat + suggested-action)
        css_calls = [c[0][0] for c in Gtk.Button.return_value.add_css_class.call_args_list]
        assert "flat" in css_calls
        assert "suggested-action" in css_calls

    def test_with_sensitive_false(self, view_helpers_module):
        """Test button with sensitive=False disables the button."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        buttons = [HeaderButton(icon_name="view-refresh-symbolic", sensitive=False)]

        create_header_button_box(buttons=buttons)

        # Verify button was set to insensitive
        Gtk.Button.return_value.set_sensitive.assert_called_with(False)

    def test_with_callback(self, view_helpers_module):
        """Test button with callback connects it to 'clicked' signal."""
        create_header_button_box = view_helpers_module.create_header_button_box
        HeaderButton = view_helpers_module.HeaderButton
        Gtk = view_helpers_module.Gtk

        callback = mock.MagicMock()
        buttons = [HeaderButton(icon_name="view-refresh-symbolic", callback=callback)]

        create_header_button_box(buttons=buttons)

        # Verify callback was connected to "clicked" signal
        Gtk.Button.return_value.connect.assert_called_once_with("clicked", callback)

    def test_with_pre_created_widget(self, view_helpers_module):
        """Test with pre-created widget appends it directly."""
        create_header_button_box = view_helpers_module.create_header_button_box
        Gtk = view_helpers_module.Gtk

        existing_button = Gtk.Button()

        box, _ = create_header_button_box(buttons=[existing_button])

        # Verify the pre-created button was appended to the box
        box.append.assert_called_once_with(existing_button)

    def test_include_spinner(self, view_helpers_module):
        """Test include_spinner adds a spinner."""
        create_header_button_box = view_helpers_module.create_header_button_box

        box, spinner = create_header_button_box(buttons=[], include_spinner=True)

        # Verify spinner was created
        assert spinner is not None


# =============================================================================
# create_refresh_header() Tests
# =============================================================================


class TestCreateRefreshHeader:
    """Tests for the create_refresh_header() function."""

    def test_creates_refresh_header(self, view_helpers_module):
        """Test create_refresh_header creates header components."""
        create_refresh_header = view_helpers_module.create_refresh_header

        header_box, spinner, button = create_refresh_header(on_refresh_clicked=mock.MagicMock())

        # Verify all components created
        assert header_box is not None
        assert spinner is not None
        assert button is not None

    def test_custom_tooltip(self, view_helpers_module):
        """Test create_refresh_header with custom tooltip sets it on button."""
        create_refresh_header = view_helpers_module.create_refresh_header

        header_box, spinner, button = create_refresh_header(
            on_refresh_clicked=mock.MagicMock(),
            tooltip="Refresh statistics",
        )

        # Verify custom tooltip was set on the refresh button
        button.set_tooltip_text.assert_called_with("Refresh statistics")

    def test_spinner_hidden_by_default(self, view_helpers_module):
        """Test spinner is hidden by default."""
        create_refresh_header = view_helpers_module.create_refresh_header

        header_box, spinner, button = create_refresh_header(on_refresh_clicked=mock.MagicMock())

        # Verify spinner starts hidden
        spinner.set_visible.assert_called_with(False)

    def test_button_has_icon(self, view_helpers_module):
        """Test button has refresh icon set."""
        create_refresh_header = view_helpers_module.create_refresh_header

        header_box, spinner, button = create_refresh_header(on_refresh_clicked=mock.MagicMock())

        # Verify refresh icon was set on the button
        button.set_icon_name.assert_called_once()

    def test_button_connects_callback(self, view_helpers_module):
        """Test button connects callback to clicked signal."""
        create_refresh_header = view_helpers_module.create_refresh_header

        callback = mock.MagicMock()
        header_box, spinner, button = create_refresh_header(on_refresh_clicked=callback)

        # Verify callback was connected to the "clicked" signal
        button.connect.assert_called_once_with("clicked", callback)
