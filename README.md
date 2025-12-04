# sid v2 — Git-like VCS

![License](https://img.shields.io/badge/license-MIT-blue.svg)


This is a more featureful educational implementation of a Git-like VCS named `sid`.
It includes:
- init, clone, config, add, status, diff, commit, reset, rm
- branch, checkout, merge, branch delete (-d/-D)
- stash, stash pop, stash list
- remote add/list, fetch, push, pull (local filesystem `file:///` remote supported)
- log, reflog (basic), tag-like refs are under refs/tags
- pyproject.toml for packaging

This is intended as an educational project. It does **not** implement the full Git protocol
and is not safe for production use.

# command list 

Repository Setup
sid init


Initializes a new SID repository in the current directory (.sid/).

⚙️ Configuration
sid config --name "Your Name"
sid config --email "you@email.com"


Sets user configuration used for commits.

Managing Changes
Add / Stage
sid add <file>
sid add <directory>
sid add .


Stages files or directories recursively.

Status
sid status


Shows:

Current branch and HEAD

Staged files

Modified but unstaged files

Diff
sid diff
sid diff --staged


sid diff → working directory vs index

sid diff --staged → index vs last commit

Commit
sid commit -m "message"


Creates a commit from staged files.

Reset (unstage)
sid reset <file>


Removes a file from the staging area.

Remove File
sid rm <file>


Deletes a file from disk and unstages it.

Branching & Checkout
List / Create Branch
sid branch
sid branch <branch-name>

Switch Branch
sid checkout <branch-name>
sid checkout -b <branch-name>


-b creates and switches to a new branch.

Delete Branch

(implemented internally; CLI deletion can be added easily)

sid branch -d <branch-name>   # safe delete (merged only)
sid branch -D <branch-name>   # force delete

Merging
sid merge <branch-name>


Fast-forward if possible

Otherwise creates a merge commit (no conflict resolver yet)

History
sid log


Prints commit history from HEAD backwards.

Stash
Save current changes
sid stash

List stashes
sid stash list

Apply & remove last stash
sid stash pop

Remotes
List remotes
sid remote

Add remote
sid remote add origin file:///absolute/path/to/repo

Fetch
sid fetch origin


Downloads remote objects and refs.

Push
sid push origin <branch>


Uploads objects and branch ref to remote.

Pull
sid pull origin <branch>


Fetch + fast-forward or merge.

(Only file:/// remotes are supported in v2)

Summary
sid init
sid config --name --email
sid add .
sid status
sid diff
sid diff --staged
sid commit -m "msg"
sid reset <file>
sid rm <file>

sid branch
sid branch <name>
sid checkout <name>
sid checkout -b <name>
sid merge <branch>

sid log

sid stash
sid stash list
sid stash pop

sid remote
sid remote add origin file:///path
sid fetch origin
sid push origin <branch>
sid pull origin <branch>
