"""Tests for the GUI application entrypoint."""

import importlib
import sys
from types import ModuleType
from unittest import mock


def _load_main_module(monkeypatch, tmp_path):
    """Import src.main with isolated XDG paths for the test."""
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    sys.modules.pop("src.main", None)
    sys.modules.pop("src.core.logging_config", None)

    import src.main as main_module

    return importlib.reload(main_module)


def _install_gui_entrypoint_fakes(monkeypatch, *, run_return_value=0, run_side_effect=None):
    """Install fake app/router modules so main() can be exercised without GTK."""
    app_instance = mock.Mock()
    app_instance.run.return_value = run_return_value
    if run_side_effect is not None:
        app_instance.run.side_effect = run_side_effect

    app_module = ModuleType("src.app")
    app_module.ClamUIApp = mock.Mock(return_value=app_instance)

    router_module = ModuleType("src.cli.router")
    router_module.CLI_SUBCOMMANDS = {"scan", "quarantine", "profile", "status", "history"}

    monkeypatch.setitem(sys.modules, "src.app", app_module)
    monkeypatch.setitem(sys.modules, "src.cli.router", router_module)

    return app_module.ClamUIApp, app_instance


class TestMainEntrypoint:
    """Tests for GUI startup behavior in src.main."""

    def test_main_returns_gui_exit_code(self, monkeypatch, tmp_path):
        """The GUI entrypoint should return the application's exit code."""
        main_module = _load_main_module(monkeypatch, tmp_path)
        app_class, app_instance = _install_gui_entrypoint_fakes(
            monkeypatch,
            run_return_value=7,
        )
        argv = ["clamui"]
        monkeypatch.setattr(sys, "argv", argv)

        exit_code = main_module.main()

        assert exit_code == 7
        app_class.assert_called_once_with()
        app_instance.run.assert_called_once_with(argv)
        app_instance.quit.assert_not_called()

    def test_main_returns_sigint_exit_code_without_traceback(self, monkeypatch, tmp_path):
        """Ctrl+C during app.run() should exit cleanly with the SIGINT code."""
        main_module = _load_main_module(monkeypatch, tmp_path)
        _, app_instance = _install_gui_entrypoint_fakes(
            monkeypatch,
            run_side_effect=KeyboardInterrupt,
        )
        argv = ["clamui"]
        monkeypatch.setattr(sys, "argv", argv)

        exit_code = main_module.main()

        assert exit_code == 130
        app_instance.run.assert_called_once_with(argv)
        app_instance.quit.assert_called_once_with()
