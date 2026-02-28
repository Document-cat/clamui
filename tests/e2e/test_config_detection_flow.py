# pyright: reportMissingImports=false

import sys
import tempfile
from pathlib import Path
from unittest import mock

import pytest

# Store original gi modules to restore later (if they exist)
_original_gi = sys.modules.get("gi")
_original_gi_repository = sys.modules.get("gi.repository")

# Mock gi module before importing to avoid GTK dependencies in tests
sys.modules["gi"] = mock.MagicMock()
sys.modules["gi.repository"] = mock.MagicMock()

from src.core.clamav_config import (
    ClamAVConfig,
    get_config_summary,
    parse_config,
    validate_config,
    validate_config_file,
    write_config,
)
from src.core.clamav_detection import (
    config_file_exists,
    detect_clamd_conf_path,
    detect_freshclam_conf_path,
    resolve_clamd_conf_path,
    resolve_freshclam_conf_path,
)
from src.core.settings_manager import SettingsManager

# Restore original gi modules after imports are done
if _original_gi is not None:
    sys.modules["gi"] = _original_gi
else:
    del sys.modules["gi"]
if _original_gi_repository is not None:
    sys.modules["gi.repository"] = _original_gi_repository
else:
    del sys.modules["gi.repository"]


DEBIAN_CLAMD_CONF = """# Debian clamd.conf
LocalSocket /var/run/clamav/clamd.ctl
FixStaleSocket true
User clamav
ScanPE true
MaxFileSize 100M
MaxScanSize 400M
"""

FEDORA_SCAN_CONF = """# Fedora scan.conf
LocalSocket /run/clamd.scan/clamd.sock
FixStaleSocket yes
User clamscan
ScanPE yes
MaxFileSize 100M
"""


@pytest.fixture
def temp_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        config_dir = base / "config"
        config_dir.mkdir(parents=True)

        debian_clamd = base / "clamd.conf"
        fedora_scan = base / "scan.conf"
        freshclam = base / "freshclam.conf"

        debian_clamd.write_text(DEBIAN_CLAMD_CONF, encoding="utf-8")
        fedora_scan.write_text(FEDORA_SCAN_CONF, encoding="utf-8")
        freshclam.write_text("DatabaseMirror database.clamav.net\n", encoding="utf-8")

        yield {
            "base": base,
            "config_dir": config_dir,
            "debian_clamd": debian_clamd,
            "fedora_scan": fedora_scan,
            "freshclam": freshclam,
        }


class TestE2EConfigDetectionNative:
    def test_e2e_detect_clamd_debian_path(self, temp_env):
        """
        E2E Test: Detect Debian/Ubuntu clamd config path in native mode.

        Steps:
        1. Force native execution path
        2. Mock file checks to only expose Debian path
        3. Verify Debian path is selected
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p == "/etc/clamav/clamd.conf",
            ),
        ):
            assert detect_clamd_conf_path() == "/etc/clamav/clamd.conf"

    def test_e2e_detect_clamd_fedora_path(self, temp_env):
        """
        E2E Test: Detect Fedora/RHEL scan.conf path in native mode.

        Steps:
        1. Force native execution path
        2. Mock file checks to only expose Fedora path
        3. Verify Fedora path is selected
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p == "/etc/clamd.d/scan.conf",
            ),
        ):
            assert detect_clamd_conf_path() == "/etc/clamd.d/scan.conf"

    def test_e2e_detect_clamd_generic_path(self, temp_env):
        """
        E2E Test: Detect generic clamd.conf path in native mode.

        Steps:
        1. Force native execution path
        2. Mock file checks to only expose generic path
        3. Verify generic path is selected
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p == "/etc/clamd.conf",
            ),
        ):
            assert detect_clamd_conf_path() == "/etc/clamd.conf"

    def test_e2e_detect_freshclam_debian_and_fedora_paths(self, temp_env):
        """
        E2E Test: Detect freshclam config for Debian and Fedora priorities.

        Steps:
        1. Force native execution path
        2. Validate Debian path detection when present
        3. Validate Fedora fallback when Debian path is absent
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p == "/etc/clamav/freshclam.conf",
            ),
        ):
            assert detect_freshclam_conf_path() == "/etc/clamav/freshclam.conf"

        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p == "/etc/freshclam.conf",
            ),
        ):
            assert detect_freshclam_conf_path() == "/etc/freshclam.conf"

    def test_e2e_no_config_found_returns_none(self, temp_env):
        """
        E2E Test: Return None when no config file exists.

        Steps:
        1. Force native execution path
        2. Mock file checks to always return False
        3. Verify both clamd and freshclam detection return None
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch("src.core.clamav_detection.os.path.isfile", return_value=False),
        ):
            assert detect_clamd_conf_path() is None
            assert detect_freshclam_conf_path() is None

    def test_e2e_clamd_priority_first_existing_path_wins(self, temp_env):
        """
        E2E Test: Prefer first matching clamd path by priority.

        Steps:
        1. Force native execution path
        2. Mock multiple paths as present
        3. Verify highest-priority Debian path wins
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=False),
            mock.patch(
                "src.core.clamav_detection.os.path.isfile",
                side_effect=lambda p: p in {"/etc/clamav/clamd.conf", "/etc/clamd.d/scan.conf"},
            ),
        ):
            assert detect_clamd_conf_path() == "/etc/clamav/clamd.conf"


class TestE2EConfigDetectionFlatpak:
    def test_e2e_config_file_exists_uses_flatpak_host_test(self, temp_env):
        """
        E2E Test: Flatpak config existence uses host check command.

        Steps:
        1. Force Flatpak execution path
        2. Mock subprocess call result as success
        3. Verify flatpak-spawn host test command is used
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=True),
            mock.patch("src.core.clamav_detection.subprocess.run") as run_mock,
        ):
            run_mock.return_value = mock.MagicMock(returncode=0)

            assert config_file_exists("/etc/clamav/clamd.conf") is True
            run_mock.assert_called_once_with(
                ["flatpak-spawn", "--host", "test", "-f", "/etc/clamav/clamd.conf"],
                capture_output=True,
                timeout=5,
            )

    def test_e2e_detect_clamd_config_through_flatpak(self, temp_env):
        """
        E2E Test: Detect clamd config through Flatpak host-aware checks.

        Steps:
        1. Force Flatpak execution path
        2. Mock config_file_exists to expose Fedora path
        3. Verify clamd detection returns the expected path
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=True),
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == "/etc/clamd.d/scan.conf",
            ),
        ):
            assert detect_clamd_conf_path() == "/etc/clamd.d/scan.conf"

    def test_e2e_detect_freshclam_config_through_flatpak(self, temp_env):
        """
        E2E Test: Detect freshclam config through Flatpak host-aware checks.

        Steps:
        1. Force Flatpak execution path
        2. Mock config_file_exists to expose Fedora path
        3. Verify freshclam detection returns the expected path
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=True),
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == "/etc/freshclam.conf",
            ),
        ):
            assert detect_freshclam_conf_path() == "/etc/freshclam.conf"

    def test_e2e_flatpak_subprocess_failure_returns_false(self, temp_env):
        """
        E2E Test: Flatpak subprocess failure gracefully returns False.

        Steps:
        1. Force Flatpak execution path
        2. Raise subprocess exception during host test
        3. Verify config_file_exists returns False
        """
        with (
            mock.patch("src.core.clamav_detection.is_flatpak", return_value=True),
            mock.patch(
                "src.core.clamav_detection.subprocess.run",
                side_effect=RuntimeError("flatpak-spawn failed"),
            ),
        ):
            assert config_file_exists("/etc/clamav/clamd.conf") is False


class TestE2EConfigResolutionWithSettings:
    def test_e2e_saved_path_used_when_file_exists(self, temp_env):
        """
        E2E Test: Resolve uses saved clamd path when it still exists.

        Steps:
        1. Persist clamd_conf_path in settings
        2. Mock config_file_exists to return True for saved path
        3. Verify resolver returns saved path without re-detecting
        """
        settings = SettingsManager(config_dir=temp_env["config_dir"])
        saved_path = "/persisted/clamd.conf"
        settings.set("clamd_conf_path", saved_path)

        with (
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == saved_path,
            ),
            mock.patch("src.core.clamav_detection.detect_clamd_conf_path") as detect_mock,
        ):
            assert resolve_clamd_conf_path(settings) == saved_path
            detect_mock.assert_not_called()

    def test_e2e_saved_path_cleared_then_redetected_when_missing(self, temp_env):
        """
        E2E Test: Invalid saved path is cleared and replaced by detected path.

        Steps:
        1. Persist stale clamd_conf_path in settings
        2. Mock saved path as missing and detector returning valid path
        3. Verify stale path is cleared and new path persisted
        """
        settings = SettingsManager(config_dir=temp_env["config_dir"])
        stale_path = "/stale/clamd.conf"
        detected_path = "/etc/clamav/clamd.conf"
        settings.set("clamd_conf_path", stale_path)

        with mock.patch(
            "src.core.clamav_detection.config_file_exists",
            side_effect=lambda p: p == detected_path,
        ):
            assert resolve_clamd_conf_path(settings) == detected_path
            assert settings.get("clamd_conf_path") == detected_path

    def test_e2e_newly_detected_path_persisted_to_settings(self, temp_env):
        """
        E2E Test: Newly detected path is persisted into settings.

        Steps:
        1. Start with empty clamd_conf_path
        2. Mock auto-detection result
        3. Verify resolver returns and persists detected path
        """
        settings = SettingsManager(config_dir=temp_env["config_dir"])
        settings.set("clamd_conf_path", "")

        with mock.patch(
            "src.core.clamav_detection.detect_clamd_conf_path",
            return_value="/etc/clamd.conf",
        ):
            assert resolve_clamd_conf_path(settings) == "/etc/clamd.conf"
            assert settings.get("clamd_conf_path") == "/etc/clamd.conf"

    def test_e2e_resolve_with_no_settings_manager(self, temp_env):
        """
        E2E Test: Resolver works when settings_manager is None.

        Steps:
        1. Call resolver with settings_manager=None
        2. Mock detection result
        3. Verify detected path is returned
        """
        with mock.patch(
            "src.core.clamav_detection.detect_clamd_conf_path",
            return_value="/etc/clamd.d/scan.conf",
        ):
            assert resolve_clamd_conf_path(None) == "/etc/clamd.d/scan.conf"

    def test_e2e_detect_save_reload_resolve_flow(self, temp_env):
        """
        E2E Test: Full detect-save-reload-resolve lifecycle using settings file.

        Steps:
        1. Resolve once to auto-detect and persist path
        2. Reload settings manager from disk
        3. Resolve again and verify saved path is reused
        """
        detected_path = str(temp_env["debian_clamd"])
        settings1 = SettingsManager(config_dir=temp_env["config_dir"])

        with mock.patch(
            "src.core.clamav_detection.detect_clamd_conf_path",
            return_value=detected_path,
        ):
            assert resolve_clamd_conf_path(settings1) == detected_path

        settings2 = SettingsManager(config_dir=temp_env["config_dir"])
        with (
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == detected_path,
            ),
            mock.patch("src.core.clamav_detection.detect_clamd_conf_path") as detect_mock,
        ):
            assert resolve_clamd_conf_path(settings2) == detected_path
            detect_mock.assert_not_called()


class TestE2EConfigParsingAfterDetection:
    def test_e2e_detect_then_parse_real_clamd_config(self, temp_env):
        """
        E2E Test: Detect real config file in temp dir, then parse and validate.

        Steps:
        1. Write realistic clamd.conf content in temp directory
        2. Patch detection path list to include temp file
        3. Detect path, parse config, and validate parsed options
        """
        custom_clamd = temp_env["base"] / "detected-clamd.conf"
        custom_clamd.write_text(DEBIAN_CLAMD_CONF, encoding="utf-8")

        with (
            mock.patch("src.core.clamav_detection._CLAMD_CONF_PATHS", [str(custom_clamd)]),
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == str(custom_clamd),
            ),
        ):
            detected = detect_clamd_conf_path()
            assert detected == str(custom_clamd)

        assert detected is not None
        parsed, error = parse_config(detected)
        assert error is None
        assert parsed is not None
        is_valid, errors = validate_config(parsed)
        assert is_valid is True
        assert errors == []

    def test_e2e_parse_modify_write_reparse_round_trip(self, temp_env):
        """
        E2E Test: Parse-modify-write-reparse round-trip preserves new values.

        Steps:
        1. Parse detected Debian-style clamd config
        2. Modify selected options in memory
        3. Write file and re-parse to verify updates persisted
        """
        config_path = temp_env["debian_clamd"]
        parsed, error = parse_config(str(config_path))
        assert error is None
        assert parsed is not None

        parsed.set_value("MaxFileSize", "150M")
        parsed.set_value("ScanPE", "false")
        ok, write_error = write_config(parsed)
        assert ok is True
        assert write_error is None

        reparsed, reparse_error = parse_config(str(config_path))
        assert reparse_error is None
        assert reparsed is not None
        assert reparsed.get_value("MaxFileSize") == "150M"
        assert reparsed.get_value("ScanPE") == "false"

    def test_e2e_parse_realistic_debian_clamd_conf(self, temp_env):
        """
        E2E Test: Parse realistic Debian clamd.conf content.

        Steps:
        1. Parse Debian clamd.conf fixture content
        2. Validate key options are parsed correctly
        3. Validate entire file using validate_config_file
        """
        parsed, error = parse_config(str(temp_env["debian_clamd"]))
        assert error is None
        assert parsed is not None
        assert parsed.get_value("LocalSocket") == "/var/run/clamav/clamd.ctl"
        assert parsed.get_value("FixStaleSocket") == "true"
        assert parsed.get_value("User") == "clamav"
        assert parsed.get_value("MaxScanSize") == "400M"

        is_valid, errors = validate_config_file(str(temp_env["debian_clamd"]))
        assert is_valid is True
        assert errors == []

    def test_e2e_parse_realistic_fedora_scan_conf(self, temp_env):
        """
        E2E Test: Parse realistic Fedora scan.conf content.

        Steps:
        1. Parse Fedora scan.conf fixture content
        2. Validate key options are parsed correctly
        3. Validate parsed structure is a ClamAVConfig object
        """
        parsed, error = parse_config(str(temp_env["fedora_scan"]))
        assert error is None
        assert parsed is not None
        assert isinstance(parsed, ClamAVConfig)
        assert parsed.get_value("LocalSocket") == "/run/clamd.scan/clamd.sock"
        assert parsed.get_value("FixStaleSocket") == "yes"
        assert parsed.get_value("User") == "clamscan"

    def test_e2e_get_config_summary_output(self, temp_env):
        """
        E2E Test: Config summary includes core metadata and options.

        Steps:
        1. Parse Debian-style config file
        2. Generate summary via get_config_summary
        3. Verify summary contains file path and expected option names
        """
        parsed, error = parse_config(str(temp_env["debian_clamd"]))
        assert error is None
        assert parsed is not None

        summary = get_config_summary(parsed)
        assert "Configuration file:" in summary
        assert "Total options:" in summary
        assert "LocalSocket" in summary
        assert "MaxFileSize" in summary


class TestE2EFreshclamDetection:
    def test_e2e_freshclam_detection_follows_clamd_pattern(self, temp_env):
        """
        E2E Test: Freshclam detection uses the same priority probing pattern.

        Steps:
        1. Mock first freshclam path missing and second existing
        2. Run freshclam detector
        3. Verify second path is selected by fallback
        """
        with mock.patch(
            "src.core.clamav_detection.config_file_exists",
            side_effect=lambda p: p == "/etc/freshclam.conf",
        ):
            assert detect_freshclam_conf_path() == "/etc/freshclam.conf"

    def test_e2e_freshclam_resolve_with_settings_persistence(self, temp_env):
        """
        E2E Test: Freshclam resolve persists detected path and reuses it.

        Steps:
        1. Resolve once with detection and persist into settings
        2. Reload settings from disk
        3. Resolve again and verify saved path is reused
        """
        detected_path = str(temp_env["freshclam"])
        settings1 = SettingsManager(config_dir=temp_env["config_dir"])

        with mock.patch(
            "src.core.clamav_detection.detect_freshclam_conf_path",
            return_value=detected_path,
        ):
            assert resolve_freshclam_conf_path(settings1) == detected_path

        settings2 = SettingsManager(config_dir=temp_env["config_dir"])
        with (
            mock.patch(
                "src.core.clamav_detection.config_file_exists",
                side_effect=lambda p: p == detected_path,
            ),
            mock.patch("src.core.clamav_detection.detect_freshclam_conf_path") as detect_mock,
        ):
            assert resolve_freshclam_conf_path(settings2) == detected_path
            detect_mock.assert_not_called()


class TestE2EMultiDistroDetection:
    def test_e2e_both_debian_and_fedora_present_debian_wins(self, temp_env):
        """
        E2E Test: Debian path wins when both Debian and Fedora configs exist.

        Steps:
        1. Mock both distro paths as present
        2. Run clamd detection
        3. Verify Debian path is chosen by priority order
        """
        with mock.patch(
            "src.core.clamav_detection.config_file_exists",
            side_effect=lambda p: p in {"/etc/clamav/clamd.conf", "/etc/clamd.d/scan.conf"},
        ):
            assert detect_clamd_conf_path() == "/etc/clamav/clamd.conf"

    def test_e2e_only_fedora_config_present(self, temp_env):
        """
        E2E Test: Fedora path is selected when only Fedora config exists.

        Steps:
        1. Mock only Fedora path as present
        2. Run clamd detection
        3. Verify Fedora path is selected
        """
        with mock.patch(
            "src.core.clamav_detection.config_file_exists",
            side_effect=lambda p: p == "/etc/clamd.d/scan.conf",
        ):
            assert detect_clamd_conf_path() == "/etc/clamd.d/scan.conf"

    def test_e2e_only_generic_config_present(self, temp_env):
        """
        E2E Test: Generic path is selected when only generic config exists.

        Steps:
        1. Mock only generic path as present
        2. Run clamd detection
        3. Verify generic path is selected
        """
        with mock.patch(
            "src.core.clamav_detection.config_file_exists",
            side_effect=lambda p: p == "/etc/clamd.conf",
        ):
            assert detect_clamd_conf_path() == "/etc/clamd.conf"
