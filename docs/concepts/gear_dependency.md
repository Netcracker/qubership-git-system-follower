# Python Dependencies in Gear

git-system-follower supports installation of Python dependencies required by a Gear's
package API scripts (`initer.py`, `updater.py`).

If a Gear has a `requirements.txt` at the root of its `git-system-follower-package/`
directory, git-system-follower installs the listed packages before executing the Gear's
scripts.

## Gear file structure

`requirements.txt`, `wheels/`, and `site-packages/` are placed at the root of
`git-system-follower-package/`, at the same level as `scripts/`:

```
git-system-follower-package/
├── package.yaml
├── requirements.txt
├── wheels/
├── site-packages/
└── scripts/
    └── ...
```

### Sample `requirements.txt`

Declares the Python packages required by the Gear's scripts:

```
requests>=2.28.0
pyyaml==6.0.1
jinja2>=3.1.0
```

### `wheels/` directory

Optional. A directory of pre-downloaded `.whl` files for air-gapped
environments. git-system-follower uses this as a fallback if a package cannot be installed
from the pip cache.

### `site-packages/` directory

Optional. An alternative local package store for `.tar.gz` packages, also used as a fallback source alongside
`wheels/`.

## How git-system-follower installs Python dependencies

git-system-follower uses `initer.py` for initialization and `updater.py` for update in the
repository. Before executing either script, git-system-follower runs
`get_package_dependency`, which:

1. Looks for `requirements.txt` at the root of `git-system-follower-package/`. If it does
   not exist, this step is skipped automatically.
2. For each package listed in `requirements.txt`, attempts to install it using the pip
   cache (`~/.cache/pip`).
3. If any packages fail to install from cache, falls back to `--find-links` across:
    - `wheels/` directory inside `git-system-follower-package/`
    - `site-packages/` directory inside `git-system-follower-package/`
    - System `site-packages` directories
   
   All with `--no-index` — no network access attempted at this stage.

!!! warning
    If fallback installation is needed but none of `wheels/`, `site-packages/`, or system
    site-packages directories exist, git-system-follower raises a `PackageApiError` and
    stops execution.

## Final Gear file structure with Python dependencies

```
<your repository>
├── git-system-follower-package/
│   ├── package.yaml
│   ├── requirements.txt
│   ├── wheels/
│   │   └── <pre-downloaded .whl files>
│   ├── site-packages/
│   │   └── <pre-downloaded .tar.gz packages>
│   └── scripts/
│       ├── 1.0.0/
│       │   ├── delete.py
│       │   ├── init.py
│       │   ├── update.py
│       │   └── templates/
│       │       └── ...
│       └── 1.1.0/
│           └── ...
```