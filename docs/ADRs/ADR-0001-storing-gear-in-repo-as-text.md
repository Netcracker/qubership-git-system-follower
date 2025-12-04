# ADR-0001 Storing Gear in a repository as text

<!-- Statuses
success "Accepted // yyyy-mm-dd"
note "Draft // yyyy-mm-dd"
failure "Rejected // yyyy-mm-dd"
-->
!!! note "Draft // 2025-12-??"

    `Technical Story`

    :   Simple structure: files that are no longer present in the gear are not deleted [#68](https://github.com/Netcracker/qubership-git-system-follower/issues/68)

    `Deciders`

    :   Vladislav Kishkin (@k1shk1n)

## Termins
* **Gear** - git package for gsf
* **`v1`, `v2`, `v3`** - gear versions
* **Complex structure** - versioned structure with `scripts/<version>/` and `update.py` for sequential upgrades. Ex. from `v1` to `v3` like `v1` → `v2` → `v3`
* **Simple structure** - non-versioned structure with `scripts/` and only `init.py`, upgrades via `--force`. Ex. from `v1` to `v3` like `v1` → `v3`
* **Blob** - in this context, a blob refers to the raw contents of a file

## Context and Problem Statement
Simple structure Gears have a simplified structure without versioning. The absence of a previous version of Gear makes it impossible to intelligently delete template files (no [3-way merge](../concepts/internals/gear-lifecycle.md#3-way-merge)) and shifts this responsibility from gsf (package manager) to Gear developer.

Files that existed in `v1` but were deleted in `v2` remain in the repository:

- `v1`: `.gitlab-ci.yml`, `README.md`, `config.yaml`
- `v2`: `.gitlab-ci.yml`, `README.md` (`config.yaml` was deleted)
- After upgrade: all three files remain → `config.yaml` is not deleted

!!! note "Additional mission"
    This solution will also help address the downgrade (rollback) question: how can we retrieve the last installed version to perform a careful migration

## Considered Options
### Download the previous version from the registry

There are two options here:

1. We download the old version of the Gear from the same registry where we download the new version.
2. We save the Gear coordinates in `.state.yaml` during installation so that we can use them for subsequent installations.

In fact, this is the most appropriate option for Simple structure, because it does not require us to store the previous version at all or introduce extra abstractions about where we get the Gear from.

However, there is a major downside: what if the Gear has been deleted from the registry? Additionally, for the first case, there is a downside if different versions are located in different registries (ex. migration from Nexus to JFrog Artifactory or different registries within the same Artifactory).

---

### Storing the structure in `.state.yaml` as `path: hash`

The idea is that the entire current file structure is recorded in `.state.yaml` like this:
```yaml
structure:
   file1: hash of blob
   dir1/file2: hash of blob
   ...
```

The flow looks like this:

Here, we install version `v1`, get the hash of each file's blob, and write this as a linear list in `.state.yaml`.
<figure markdown="span">
  ![v1 Structure in .state.yaml](assets/structure-in-state-yaml.drawio.png)
  <figcaption>Install v1</figcaption>
</figure>

After this, we want to install version `v2`. gsf will compare the current state in the repository (generating the hashes of blobs) with what is in `.state.yaml`. If the hashes do not match, it means the user made changes (the hash in `.state.yaml` remains the same); if they do match, there were no changes and gsf can safely update this file to the new version from `v2` (the hash is updated).
<figure markdown="span">
  ![v2 Structure in .state.yaml](assets/structure-in-state-yaml2.drawio.png)
  <figcaption>Install v2</figcaption>
</figure>

With a large number of files in a Gear and with `.state.yaml` being encrypted, every line in the file would be updated on each installation (ex. `sops`). This could cause the size of the repository to grow rapidly.

Additionally, the correctness of this approach is unclear in the following case:  
installed `v1` → user made changes in a file → installed `v2` → user reverted the changes (so now we have one file from `v1` alongside other files from `v2`) → then install `v3`.

---

### Storing the entire previous version in the repository as full directory (plain text)

In this approach, the previous version of the Gear is fully stored in the repository, using text files that replicate the structure of the actual Gear. Effectively, this method creates **a remote cache** inside the repository, allowing for quick retrieval or deletion of Gears that have previously been used in this repository.

/// html | div[style='float: left; width: 48%;']
Pros:

- Text format - makes it easy to compare versions (`git diff`);
- Local access to versions, no registry required;
- Unused versions can be easily deleted;
- Standard git commands work as usual;
- Files can be viewed with standard tools.
///

/// html | div[style='float: right;width: 4%;']
///

/// html | div[style='float: right;width: 48%;']
Cons:

- Repository size can grow quickly with a large number of versions;
- Directory gets cluttered with additional files;
- Harder to manage in large projects;
- You cannot restore only specific Gears - the entire branch is copied.
///

/// html | div[style='clear: both;']
///

=== "Option A: separate directory"
    
    The Gear is stored unpacked in a special directory in `.gsf-snapshots/` like  `.state.yaml`.
    
    Details:
    
    - All Gears are separate folders at the root of the repository
    - Removing a snapshot is as simple as deleting the desired folder
    - With many versions of gears, the directory can become cluttered quickly
    - The same versions may be duplicated in different branches

=== "Option B: separate git branch"
    
    Gears are stored in a separate orphan branch, such as `gsf/gears`, completely isolated from the main development history.
    
    Details:
    
    - The working directory remains clean
    - No duplication of identical versions across branches
    - To work with snapshots, you have to switch to another branch
    - All snapshots can be quickly deleted using git

---

### Storing the entire previous version in the repository as simple line

This approach creates a **remote cache** within the repository too  as in the [previous section](#storing-the-entire-previous-version-in-the-repository-as-full-directory-plain-text), allowing quick retrieval or deletion of Gears that have been used in this repository. One option is to use a method similar to Helm: store the entire Gear as a protobuf object + compress + encode in base64 or just compress + encode in base64 (in both cases resulting: a large single string).

To work with protobuf, we'll need the `protobuf` library (size: 1.6MB) and the `protobuf-compiler` (size: 18.7MB), as well as some overhead related to using it: developers must understand this protocol, generate or store a prepared `.proto` file (see [Protocol Buffers Documentation](https://protobuf.dev/)), fields in the file may change, and it's necessary to consider support for backward compatibility.

A comparison of Gear serialization sizes using yaml/json vs protobuf:

??? example "For test Gear `tests/gears/complex`"
    | Format     | Raw      | Gzip      | Base64    |
    |------------|----------|-----------|-----------|
    | yaml/json  | 11.8 KB  | 2.0 KB    | 2.7 KB    |
    | Protobuf   | 8.8 KB   | 1.2 KB    | 1.6 KB    |
    ||
    | **Savings**| -25% (-3.0 KB) | -39% (-0.8 KB) | -41% (-1.1 KB) |

??? example "For a big Gear"
    | Format     | Raw      | Gzip      | Base64    |
    |------------|----------|-----------|-----------|
    | yaml/json  | 2.3 MB   | 325.4 KB  | 433.8 KB  |
    | Protobuf   | 1.7 MB   | 131.1 KB  | 174.8 KB  |
    ||
    | **Savings**| -25% (-589 KB) | -60% (-194 KB) | -60% (-259 KB) |

Actual space saving in `.state.yaml`: protobuf a 40-60% size reduction compared to yaml/json.

/// html | div[style='float: left; width: 48%;']
Pros:

- More compact than plain text because of protobuf + gzip
///

/// html | div[style='float: right;width: 4%;']
///

/// html | div[style='float: right;width: 48%;']
Cons:

- No native `git diff`; manual decoding needed to view Gear content
- Requires protobuf and a `.proto` schema in protobuf + gzip + base64 case
- Can be used as a distributed cache with fallback
///

/// html | div[style='clear: both;']
///

#### Option A: git notes with refs hierarchy

Serialize the Gear in protobuf, compress with gzip, encode in base64, and store it in git notes with a hierarchical refs structure.

??? question "What are git notes"
    [Git notes](https://git-scm.com/docs/git-notes) provide a way to store additional metadata (text or binary) for commits without changing the commits themselves. Notes are stored in special refs (for example, `refs/notes/commits` or a custom namespace like `refs/notes/gsf-gears`) and are regular Git objects (blobs) linked to a commit SHA through a special tree in the notes ref.

    Key technical details:

    - **Storage:** Notes are standard Git blobs stored in `.git/objects/`. Refs in `.git/refs/notes/` point to a commit object containing a tree object that maps commit SHAs to note blob SHAs.
    - **Not in working directory:** Notes do not appear in `git checkout` and do not take up space in the working directory.
    - **Independent from history:** Adding or changing notes does not alter the commit SHA of the main history; notes can be attached to existing commits after the fact.
    - **Refs hierarchy:** You can create custom namespaces instead of the default `refs/notes/commits`, such as `refs/notes/gsf-gears/my-package/1.0.0`.
    - **Synchronization:** Notes are NOT synchronized automatically by `git push/pull`; you must explicitly specify the ref: `git push origin refs/notes/*`.

Usage structure for gears:

```
refs/notes/gsf-gears/
├─ my-package/
│  ├─ 1.0.0 → blob: base64(gzip(protobuf(gear)))
│  ├─ 2.0.0 → blob: base64(gzip(protobuf(gear)))
│  └─ 3.0.0 → blob: base64(gzip(protobuf(gear)))
└─ another-package/
   └─ 1.0.0 → blob: base64(gzip(protobuf(gear)))
```

`.state.yaml` contains only links or hashes:
```yaml
packages:
  - name: my-package
    version: "3.0.0"
    gear: "refs/notes/gsf-gears/my-package/3.0.0"
```

/// html | div[style='float: left; width: 48%;']
Pros:

- Doesn't take up space in the working directory
- All Gears are located in one place for the entire repository
- Fast searching: `git for-each-ref`
- Easy to delete outdated items: `git update-ref -d`
- Selective fetch of required Gears
- Namespace isolation
- `.state.yaml` stays compact-contains only links
- Repository cleanup with `git gc` after removing old gears
///

/// html | div[style='float: right;width: 4%;']
///

/// html | div[style='float: right;width: 48%;']
Cons:

- Separate `git push origin refs/notes/gsf-gears/*` needed to sync notes
- Separate `git fetch origin refs/notes/gsf-gears/*` needed to fetch notes
- Git notes are a less widely known mechanism - can be unfamiliar to users
- Notes per commit. This means one installation = one gear
- Notes are tied to commits; if a commit is deleted, its note is orphaned and removed by `git notes prune`
///

/// html | div[style='clear: both;']
///

#### Option B: Embedded in `.state.yaml`

Serialize the Gear into protobuf, compress it with gzip, encode in base64, and embed it directly into `.state.yaml`:

```yaml
packages:
  - name: my-package
    version: "1.0.0"
    snapshot: "H4sIAAAAAAAAA+1XTW..."  # base64(gzip(protobuf(gear)))
```

/// html | div[style='float: left; width: 48%;']
Pros:

- Everything in a single file
- `.state.yaml` remains the single source of truth
- Easy to synchronize (git push/pull)
///

/// html | div[style='float: right;width: 4%;']
///

/// html | div[style='float: right;width: 48%;']
Cons:

- Encrypting `.state.yaml` with `sops` or similar tools completely changes the `packages[].snapshot` section - fast growth of git history
- Many Gears make `.state.yaml` large
///

/// html | div[style='clear: both;']
///

---

### Do not store the previous version at all

In principle, Simple structure should not allow tracking the previous state, and if you need to delete old files, you should use the Complex structure. However, as mentioned earlier, this shifts the responsibility onto the Gear developer.

## Decision Outcome

## Potential Risks

## Positive Consequences

## Negative Consequences