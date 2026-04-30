# Quarantine Restore/Delete Redesign

**Status**: Designed, not implemented. Authored 2026-04-30.
**Bugs subsumed**: VULN-003, BUG-006, VULN-004, BUG-007 (all flagged by /aura review on 2026-04-30 across aegis + debug-agent).

## TL;DR

The four bugs all stem from one root cause: the restore/delete pipeline treats DB and FS as independent steps with no atomicity contract, and uses high-level `shutil`/`os.chmod` primitives that silently follow symlinks and accept tainted permission bits. The fix is a single redesigned two-phase commit pipeline (DB sentinel → FS op via `O_NOFOLLOW`/`O_EXCL` → DB finalize) with a permission mask at quarantine time, plus a list-tracked connection pool counter — replacing four ad-hoc patches with one consistent transactional model.

## Bugs

### VULN-003 (HIGH security) — TOCTOU on restore
`src/core/quarantine/file_handler.py:784-808`. `destination_obj.exists()` and `is_symlink()` checks, then `shutil.move(quarantine_path, original_path)`. Window between check and move: attacker (or user via script) can place a symlink at `original_path` pointing to `~/.bashrc` or similar; `shutil.move` follows it, overwriting target with quarantined content.

### BUG-006 (MED correctness) — Restore non-atomic
`src/core/quarantine/manager.py:303-313` and `delete_file:387-397`. File moved out of quarantine first, then `_database.remove_entry`. If DB delete fails, file is back at original path while DB still references missing quarantine path. Same pattern in `delete_file`.

### VULN-004 (MED security) — Unmasked chmod
`src/core/quarantine/file_handler.py:811`, `database.py:289,313-322`. `original_permissions` read from SQLite as INTEGER, applied via `os.chmod(original_path, original_permissions)`. No mask: setuid/setgid/sticky bits restorable. DB tampering would let attacker plant 0o6755 on restore.

### BUG-007 (MED correctness) — Connection pool counter drift
`src/core/quarantine/connection_pool.py:326-347`. `close_all` decrements `_total_connections` only for queued conns. Connections checked out close via `release()` after `_closed`, but the early-return at line 211 skips the decrement. After lifecycle, counter > 0 even though no real conns exist.

## Recommended Design

### 1. Atomicity strategy: file-first via atomic-rename + DB state sentinel

Two-phase commit using a `state` column on the existing `quarantine` table:
- `set_state(id, 'pending_restore')` →
- atomic FS op (see §2) →
- `os.unlink(quarantine_path)` →
- `set_state(id, 'active')` then `remove_entry(id)`.

Same pattern for delete with `pending_delete`. Recovery sweep on `QuarantineManager.__init__` reconciles any rows left in pending states.

### 2. TOCTOU defense — hybrid `os.link` + `O_NOFOLLOW`

Capture parent dir as fd once; all subsequent ops use `dir_fd=parent_fd` to defeat path-traversal TOCTOU.

```python
def _atomic_create_at_destination(self, src: Path, dst: Path, mode: int) -> None:
    """Create dst from src atomically, refusing pre-existing files & symlinks.
    Same-fs: hardlink (atomic). Cross-fs: O_NOFOLLOW|O_EXCL + copy + rename."""
    parent_fd = os.open(dst.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        try:
            os.link(src, dst, follow_symlinks=False)
            os.chmod(dst, mode)  # mode already masked to 0o777
            return
        except OSError as e:
            if e.errno not in (errno.EXDEV, errno.EPERM):
                raise

        tmp_name = f".{dst.name}.{secrets.token_hex(8)}.partial"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC
        fd = os.open(tmp_name, flags, mode, dir_fd=parent_fd)
        try:
            with open(src, "rb") as r, os.fdopen(fd, "wb", closefd=False) as w:
                shutil.copyfileobj(r, w, length=self.HASH_BUFFER_SIZE)
                w.flush()
                os.fsync(fd)
            os.rename(tmp_name, dst.name, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
        finally:
            with contextlib.suppress(OSError):
                os.close(fd)
    finally:
        os.close(parent_fd)
```

### 3. Permissions — mask at write AND read

```python
PERMISSION_MASK = 0o777  # discard setuid/setgid/sticky

# add_entry: original_permissions = original_permissions & PERMISSION_MASK
# from_row: ... (row[7] & PERMISSION_MASK) if len(row) > 7 else 0o644
# Schema: original_permissions INTEGER NOT NULL DEFAULT 420
#         CHECK (original_permissions BETWEEN 0 AND 511)
```

### 4. Connection pool — `weakref.WeakSet`

```python
self._all_conns: weakref.WeakSet[sqlite3.Connection] = weakref.WeakSet()
# acquire() → after creating: self._all_conns.add(conn)
# release(conn) when closed: take _lock, conn.close(), self._all_conns.discard(conn)
# close_all(): drain queue + iterate list(self._all_conns) snapshot
# get_stats(): active_count = max(0, len(self._all_conns) - self._pool.qsize())
```

GC self-corrects; "phantom active" becomes structurally impossible.

### 5. Schema migration v1 → v2

```sql
BEGIN IMMEDIATE;
  CREATE TABLE quarantine_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    quarantine_path TEXT NOT NULL UNIQUE,
    threat_name TEXT NOT NULL,
    detection_date TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash TEXT NOT NULL,
    original_permissions INTEGER NOT NULL DEFAULT 420
      CHECK (original_permissions BETWEEN 0 AND 511),
    state TEXT NOT NULL DEFAULT 'active'
      CHECK (state IN ('active','pending_restore','pending_delete'))
  );
  INSERT INTO quarantine_v2
    SELECT id, original_path, quarantine_path, threat_name, detection_date,
           file_size, file_hash, (original_permissions & 511), 'active'
    FROM quarantine;
  DROP TABLE quarantine;
  ALTER TABLE quarantine_v2 RENAME TO quarantine;
  CREATE INDEX idx_quarantine_detection_date ON quarantine(detection_date);
  CREATE INDEX idx_quarantine_original_path  ON quarantine(original_path);
  CREATE INDEX idx_quarantine_state ON quarantine(state) WHERE state != 'active';
COMMIT;
```

Gate on `PRAGMA user_version`: only bump 1→2 after COMMIT. Detect orphan `quarantine_v2` from interrupted migration and DROP before retry.

### 6. Recovery sweep (on `QuarantineManager.__init__`)

Query rows in `('pending_restore', 'pending_delete')`. For each:

**`pending_restore`**:
- Quarantine missing AND original exists with matching hash → `remove_entry(id)`, log INFO.
- Quarantine missing AND original exists with **mismatched hash** → log structured WARNING (`extra={"event": "quarantine_restore_hash_mismatch", ...}`), call `notification_manager.send` if available, leave row pending for manual resolution. **Do NOT auto-restore** — design decision (security tool should not silently overwrite user-modified content).
- Quarantine present AND original absent → reset to `active`, log INFO.
- Both missing → reset to `active`, log ERROR.

**`pending_delete`**:
- Quarantine missing → `remove_entry(id)`.
- Quarantine present → re-attempt `os.unlink`, then `remove_entry`.

## Files to Modify

| File | Changes | LoC |
|------|---------|-----|
| `src/core/quarantine/file_handler.py` | New `_atomic_create_at_destination`; rewrite `restore_from_quarantine` (~784-849); mask permissions on chmod | ~120 |
| `src/core/quarantine/database.py` | New `state` column; `set_state`, `get_pending_entries`; mask in `add_entry`/`from_row`; v2 migration; CHECK constraints | ~80 |
| `src/core/quarantine/manager.py` | Rewrite `restore_file` (303-319) and `delete_file` (366-403) with sentinel pattern; add `recover_pending_operations()` | ~100 |
| `src/core/quarantine/connection_pool.py` | Replace counter with `WeakSet`; rewrite `acquire`, `release`, `close_all`, `get_stats` (180-347) | ~60 |
| `tests/core/test_quarantine_manager.py` | Update existing assertions; add recovery tests | ~150 |
| `tests/core/test_quarantine_database.py` | Migration test, mask test, state-column tests | ~80 |

## Files to Add

| File | Purpose |
|------|---------|
| `tests/core/test_quarantine_security.py` | VULN-003/VULN-004 regression — symlink TOCTOU, setuid mask, cross-fs harness |
| `tests/core/test_quarantine_recovery.py` | Crash-recovery — sentinel state transitions, hash-mismatch logging |

## Resolved Open Questions

| # | Question | Decision |
|---|----------|----------|
| 1 | Hash-mismatch on `pending_restore` recovery | Surface to user (log structured warning + notify if available); do NOT auto-restore. Auto-overwriting user-modified content is the kind of failure mode that destroys trust in security tools. |
| 2 | Quarantine path on tmpfs (Flatpak)? | Defer — kraken to verify by reading `quarantine_config.py` at implementation. Affects test matrix only. |
| 3 | Backwards-compat with CHECK constraint | Accept; document in release notes. Old code masked `& 0o777` before insert per `database.py:289` so no real downgrade hazard. |
| 4 | Recovery-sweep telemetry | Log structured event only. No UI badge until crash patterns emerge in the wild. |
| 5 | `uuid` vs `secrets.token_hex(8)` for partial-file names | `secrets.token_hex(8)` — slightly better entropy semantics, no system-time leakage. |

## Test Plan

**VULN-003**:
- `test_restore_refuses_symlink_at_destination`
- `test_atomic_create_O_NOFOLLOW_rejects_symlink_dst`
- `test_cross_filesystem_fallback` (monkeypatch `os.link` to raise `OSError(EXDEV)`)

**BUG-006**:
- `test_restore_db_failure_leaves_pending_restore_state`
- `test_recover_pending_restore_with_matching_hash_finalizes`
- `test_recover_pending_restore_with_mismatched_hash_logs_warning`
- `test_recover_pending_delete_finalizes`
- `test_delete_db_failure_does_not_unlink_prematurely`

**VULN-004**:
- `test_restore_strips_setuid_bits`
- `test_add_entry_masks_setuid_at_write_time`
- `test_schema_check_rejects_invalid_perms`

**BUG-007**:
- `test_close_all_zeros_active_count`
- `test_concurrent_close_during_checkout`
- `test_weakref_self_cleanup`

## Rollout & Risks

- **Schema migration**: v1→v2 in `BEGIN IMMEDIATE`. Interrupted mid-migration leaves `quarantine_v2` orphan; init detects and DROPs before retry. PRAGMA user_version flips only on COMMIT.
- **Cross-filesystem**: Flatpak overlayfs typically same-fs; native Debian commonly splits `/home` from `/var/lib`. `os.link` → NOFOLLOW-copy fallback handles both. CI matrix should mount a separate tmpfs for the quarantine dir.
- **Existing user impact**: rows with stored permissions > 511 get masked to `0o777` on migration. No data loss; no UI-visible change.
- **kill -9 mid-restore**: `pending_restore` rows reconciled at startup. Three outcomes documented in §6.
- **Performance**: extra DB round-trip per op (~100µs) vs. existing ~5ms FS ops. Negligible.
- **Encryption** (out of scope): quarantine files stored as-is on disk. Defeats AV scans of quarantine dir; revisit when DB tampering becomes a real threat.

## Out of Scope

- VirusTotal scan-cache (separate subsystem)
- Quarantine file encryption (separate hardening, key-management questions)
- UI-side dialog for hash-mismatch recovery (logging now; UI follow-up tracked separately)

## Implementation Notes

When kraken implements this:
- TDD red-then-green order. Tests committed in same diff as implementation.
- Use relative imports per project convention.
- Run full suite + ruff + format before reporting.
- Verify v1→v2 migration runs cleanly when test fixture has a v1 DB.
- **No AI attribution** in code, comments, or commit messages.
