# ClamUI TrayIntegration Tests
"""Unit tests for tray window visibility toggling behavior."""

from unittest import mock

from src.tray_integration import TrayIntegration


def _make_app(active_window):
    app = mock.MagicMock()
    app.props.active_window = active_window
    app._tray_indicator = mock.MagicMock()
    return app


def test_toggle_window_hides_visible_window_and_updates_label():
    """Visible window should be hidden and menu label updated."""
    win = mock.MagicMock()
    win.is_visible.side_effect = [True, False]
    app = _make_app(win)

    integration = TrayIntegration(app)
    integration.toggle_window()

    win.hide_window.assert_called_once()
    win.show_window.assert_not_called()
    app._tray_indicator.update_window_menu_label.assert_called_once_with(visible=False)


def test_toggle_window_shows_hidden_window_and_updates_label():
    """Hidden window should be shown and menu label updated."""
    win = mock.MagicMock()
    win.is_visible.side_effect = [False, True]
    app = _make_app(win)

    integration = TrayIntegration(app)
    integration.toggle_window()

    win.show_window.assert_called_once()
    win.hide_window.assert_not_called()
    app._tray_indicator.update_window_menu_label.assert_called_once_with(visible=True)


def test_toggle_window_uses_existing_hidden_window_when_no_active_window():
    """Toggle should recover a hidden window from app window list."""
    win = mock.MagicMock()
    win.is_visible.side_effect = [False, True]
    app = _make_app(None)
    app.get_windows.return_value = [win]

    integration = TrayIntegration(app)
    integration.toggle_window()

    app.activate.assert_not_called()
    win.show_window.assert_called_once()
    app._tray_indicator.update_window_menu_label.assert_called_once_with(visible=True)


def test_toggle_window_activates_app_when_no_window_is_active():
    """If no window is available, app should be activated before toggling."""
    win = mock.MagicMock()
    win.is_visible.side_effect = [False, True]
    app = _make_app(None)
    app.get_windows.side_effect = [[], [win]]

    integration = TrayIntegration(app)
    integration.toggle_window()

    app.activate.assert_called_once()
    win.show_window.assert_called_once()
