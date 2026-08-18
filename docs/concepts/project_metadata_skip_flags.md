# Project metadata skip flags

The `--skip-project-description` and `--skip-project-icon` flags of the
[`install`](../cli_reference/install.md) and [`uninstall`](../cli_reference/uninstall.md)
commands control how git-system-follower reacts when the GitLab project description or
icon (avatar) no longer matches what a v2 gear declares in `package.yaml`.

By default a mismatch is a **hard error**: the command exits with code 1 and the
operation is aborted. Passing the corresponding flag demotes that field to a
**warning**: the operation continues.

| Flag | Effect |
|---|---|
| `--skip-project-description` | Description mismatch warns instead of exits |
| `--skip-project-icon` | Icon mismatch warns instead of exits |

The two flags are independent: you can skip either field, both, or neither.

## How the check works

The check is **driven by the state file**, not by `package.yaml`:

1. A v2 gear that declares **both** `description` and `icon` triggers project
   metadata synchronization on `install`/`update`, and git-system-follower records the
   synchronized values in `.state.yaml` under `project_metadata`
   (`description`, `icon`, `icon_hash`).
2. On **every subsequent run** (install/update/rollback/uninstall) the recorded values
   are compared against the live GitLab project:
   * `description` is compared with the project description.
   * `icon_hash` is compared with the hash of the current project avatar. If the
     recorded `icon` is empty, the project must have **no** avatar at all.
3. A mismatch means the metadata was modified externally after the gear was installed.
   Without the skip flags the command exits; with them it warns and continues.

Because the check reads the *previous* state, it only becomes active **one run after**
the metadata was first recorded. The very run that introduces the metadata is never
blocked by it.

## When the check does NOT apply

The check is skipped entirely when the state file has no `project_metadata` entry for
the package. This is the case for:

* **v1 gears** — v1 has no project metadata concept.
* **v2 gears without `description` or `icon`** — when either key is missing, no metadata
  is recorded (partial metadata, e.g. description without icon, is ignored as well).
* **Fresh installs** — there is no state yet, so there is nothing to compare against.
  The skip flags are no-ops on a fresh install.

In all these cases the flags have no effect: there is no metadata to validate.

## Scenarios

### v2 gear WITH `description` and `icon`

**Fresh install (with both flags):**
* No state file exists yet → no metadata check → the flags are no-ops.
* The description and icon are synchronized to GitLab and recorded in `.state.yaml`.
* Install completes normally. Note: metadata synchronization requires an
  **Owner** token (see [Token Permissions](token_permissions.md)); the skip flags do
  not remove this requirement.

**Update or uninstall later:**

| State since install | Without flags | With flags |
|---|---|---|
| Nothing changed | proceeds | proceeds (no warning) |
| Description/icon edited externally | exits with code 1 | warns, proceeds |

* On **update** with the flags: the run proceeds and re-synchronizes the description/icon
  back to the `package.yaml` values, overwriting the external edits.
* On **uninstall** with the flags: the run proceeds; the GitLab description/icon are
  left untouched (the delete path does not synchronize metadata).

### v2 gear WITHOUT `description`/`icon`

**Fresh install (with both flags):**
* No metadata check runs → the flags are no-ops.
* Nothing is recorded in `.state.yaml` (`project_metadata` stays absent).
* The description is not touched. An avatar that already exists on the project is
  **left untouched** — git-system-follower never removes an avatar it did not manage.

**Update or uninstall later:**
* The state still has no `project_metadata` → the check is skipped → the flags are
  irrelevant.
* Update: the description stays untouched; an avatar that appeared externally is not
  removed.
* Uninstall: proceeds normally; description/icon are not modified.

### Migration: v1 → v2, `description`/`icon` added

A gear that was v1 and switches to v2 while adding `description` and `icon`:

* The **upgrade run** reads the *old* v1 state entry, which has no `project_metadata` →
  the check is skipped → the migration is **not blocked** by metadata validation, with
  or without the flags.
* During the upgrade the scripts synchronize the description/icon and record
  `project_metadata` in the new state.
* **First real impact**: the upgrade now requires an **Owner** token (metadata
  synchronization). If the token is only Maintainer or lower, the upgrade fails at the
  permission check — this is not affected by the skip flags.
* From the **next** run on, the metadata check is active: external description/icon
  drift exits unless the corresponding skip flag is passed.

### Migration: v1 → v2 without metadata for several versions, then added later

A gear that went v1 → v2 without `description`/`icon` for a few versions, and only later
added them:

* All intermediate v2 versions: no `project_metadata` is recorded, the check stays
  inactive, and the flags are irrelevant. External description/icon drift is not
  detected during this whole window.
* The version that *adds* `description`/`icon`: the check is again skipped at read time
  (the previous state still has no `project_metadata`), the update synchronizes the
  metadata and records it.
* The check only becomes active from the run **after** that version is installed.

## What the flags do NOT affect

The skip flags only relax the project metadata validation. They do **not** bypass:

* The state file hash integrity check.
* The CI/CD variables and webhook hash checks.
* The token permission check (description/icon sync still requires Owner).

## Related

* [apiVersion v2](api_version_list/v2.md) — project metadata synchronization
* [Token Permissions](token_permissions.md) — required access levels
