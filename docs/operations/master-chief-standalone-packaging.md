# Chief standalone packaging (P0.3d)

```text
Status: candidate built and verified in isolation; NOT installed
Production: unchanged (Chief.app asar 529c221c…, cosd PID 34750)
```

Chief.app no longer needs the development checkout at runtime. The Python core ships inside the
bundle as an immutable, versioned resource.

## Runtime layout

```text
Chief.app/Contents/Resources/runtime/
    cos              launcher (Python 3.12 resolution + import from ./py)
    cosd             launcher
    py/cos/          packaged cos sources
    py/cosd/         packaged cosd sources
    manifest.json    commit, version, python requirement, dependency pin, artifact hashes
```

`scripts/stage-runtime.mjs` stages it, hashes both trees, refuses to stage if the launchers mention
the checkout, and runs as part of `npm run package`. `electron-builder.yml` ships it via
`extraResources`.

## Runtime selection

`src/main/config.ts` prefers `<Resources>/runtime/cos` whenever `process.resourcesPath` is set. A
`cosPath` in `desktop.json` is honoured **only** when no packaged runtime exists, so a stale
development path cannot pull a packaged build back to the checkout. `cosd` is derived from `cos` by
the existing sibling rule.

## Python strategy

Evaluated:

| Option | Verdict |
| --- | --- |
| Bundled Python interpreter | Deferred — large, and relocatable-venv assumptions need their own testing |
| **Managed external env (`~/.chief-runtime`)** | **Selected** for this candidate |
| System Python | Rejected — must never be used silently |

The launcher resolves `CHIEF_PYTHON` → `~/.chief-runtime/python` → `python3.12` → Homebrew, verifies
it is Python 3.12, and fails with a clear message otherwise. There is no silent fallback.

## Provenance

`manifest.json` records: app name/version, runtime version (`<app>+<commit>`), source commit and
branch, dirty flag, Python requirement and resolution order, dependency pin, architecture, per-tree
file counts and SHA-256, build timestamp. No secrets.

## Verification (performed)

Candidate: `apps/chief-desktop/release/p0.3d-candidate/mac-arm64/Chief.app`, asar
`d52753cb18affb4e1a3546120976c0bf1397d02a8bfea8c98226d6ac860c7dfe`, arm64, signed Apple
Development (Team 98F559Y354), hardened runtime, not notarized.

The bundle was copied to a temporary directory and run with `env -i` (no `PYTHONPATH`), `cwd=/`:

| Check | Result |
| --- | --- |
| Repository path in packaged runtime | none (`grep` over launchers, sources, manifest) |
| Packaged `cos --version` | `cos 0.1.0-m1` |
| Packaged `cosd start` on temp state/port | pid assigned, loopback |
| `cosd health` | `{"ok": true, ...}` |
| Task create + list | `QUEUED`, total 1 |
| `cosd stop` | `{"ok": true, "stopped": true}` |

## State compatibility

The runtime uses the existing `~/Library/Application Support/ChiefOfStaff` state, token format,
SQLite schema (v2 plus additive reservation tables), sessions, audit and device registry. No
migration is performed by this mission; the packaged runtime opens the same database with the same
`CREATE TABLE IF NOT EXISTS` forward behaviour.

## Credential release gates carried forward

1. **Rotated old-secret orphan window (low, accepted).** A crash between rotation commit and cleanup
   recording can leave an inert secret in the provider; authentication requires `status='active'`.
2. **`registry.rotate_credential()` returns `public_dict()` without the new token.** This is a real
   contract gap for any caller that needs to deliver the new credential. No enabled API path in this
   product uses it that way today (the CLI/registry path returns metadata only), but it must be
   fixed before rotation is exposed to clients. Not changed here to avoid altering a credential API
   contract outside packaging scope.

Pairing and remote enrollment remain disabled.

## Signing and notarization

Ad-hoc path is Apple Development signing with hardened runtime. Notarization requires Developer ID
credentials and an owner-approved account interaction; it is **not** performed. Procedure for a later
mission: sign with the Developer ID identity, `notarytool submit --wait`, staple, then verify with
`spctl -a -vv`.

## Rollback and installation (not performed here)

Installation is a separate owner-approved mission: quit Chief, move the current bundle aside,
`ditto` the candidate into `/Applications`, verify the asar hash and signature, launch once. Rollback
restores the preserved bundle. The candidate is not installed and production is untouched.

## Known limitations

- Python is a prerequisite (`~/.chief-runtime` or a 3.12 interpreter); it is not bundled yet.
- Not notarized; another Mac would see a Gatekeeper warning.
- The runtime manifest records `dirty: true` when built from an uncommitted tree.
