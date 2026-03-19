"""Regression tests for the local development launcher script."""

import os
import stat
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "local-run.sh"


def _write_fake_uv(bin_dir: Path) -> None:
    fake_uv = bin_dir / "uv"
    fake_uv.write_text('#!/bin/sh\nprintf \'%s\\n\' "$*" >> "$TMP_UV_LOG"\nexit 0\n')
    fake_uv.chmod(fake_uv.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def test_run_flag_is_not_forwarded_to_clamui(tmp_path):
    """`--run` should stay internal to the launcher and not reach the app."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    _write_fake_uv(bin_dir)

    log_path = tmp_path / "uv.log"
    scan_target = "/tmp/clamui-scan-target"

    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["TMP_UV_LOG"] = str(log_path)

    result = subprocess.run(
        ["bash", str(SCRIPT_PATH), "--run", "--virustotal", scan_target],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    commands = log_path.read_text().splitlines()
    assert commands[-1] == f"run --no-sync clamui --virustotal {scan_target}"
    assert "--run" not in commands[-1]
