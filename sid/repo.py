"""High-level repository operations implementing many Git-like features (simplified)."""
from pathlib import Path
import json, time, shutil
from .objects import ObjectStore
from .index import Index
from .refs import read_ref, write_ref, refs_dir, SID_DIR
from typing import Optional, List, Dict, Any
import difflib

class Repo:
    def __init__(self, path: str = '.'):
        self.workdir = Path(path).resolve()
        self.sid_dir = self.workdir / SID_DIR
        self.objects = ObjectStore(self.workdir)
        self.index = Index(self.workdir)
        self._ensure_structure()

    def _ensure_structure(self):
        self.sid_dir.mkdir(parents=True, exist_ok=True)
        (self.sid_dir / 'refs' / 'heads').mkdir(parents=True, exist_ok=True)
        (self.sid_dir / 'refs' / 'remotes').mkdir(parents=True, exist_ok=True)
        if not (self.sid_dir / 'HEAD').exists():
            (self.sid_dir / 'HEAD').write_text('refs/heads/master')

    def init(self):
        self._ensure_structure()
        (self.sid_dir / 'config').write_text(json.dumps({'user':{}}))
        print(f'Initialized empty sid repository in {self.sid_dir}')

    def head_ref(self) -> str:
        return (self.sid_dir / 'HEAD').read_text().strip()

    def head_oid(self) -> Optional[str]:
        ref = self.head_ref()
        return read_ref(self.workdir, ref)

    def update_ref(self, ref: str, oid: Optional[str]):
        write_ref(self.workdir, ref, oid or '')

    def set_config(self, key: str, value: str):
        cfgf = self.sid_dir / 'config'
        cfg = json.loads(cfgf.read_text()) if cfgf.exists() else {}
        cfg.setdefault('user', {})[key] = value
        cfgf.write_text(json.dumps(cfg, indent=2))

    def get_config(self) -> Dict[str, str]:
        cfgf = self.sid_dir / 'config'
        if cfgf.exists():
            return json.loads(cfgf.read_text())
        return {}

    def add(self, path: str):
        p = self.workdir / path
        if not p.exists():
            raise FileNotFoundError(path)
        if p.is_dir():
            # stage files recursively
            for f in p.rglob('*'):
                if f.is_file() and not str(f).startswith(str(self.sid_dir)):
                    rel = str(f.relative_to(self.workdir))
                    oid = self.objects.write_blob(f.read_bytes())
                    self.index.stage(rel, oid)
        else:
            oid = self.objects.write_blob(p.read_bytes())
            rel = str(p.relative_to(self.workdir))
            self.index.stage(rel, oid)

    def status(self):
        staged = self.index.as_dict()
        head = self.head_oid()
        print('On', self.head_ref(), '->', head)
        if staged:
            print('Staged files:')
            for p in staged:
                print('  ', p)
        else:
            print('No files staged.')
        # unstaged (changed files)
        changed = []
        for p in self.workdir.rglob('*'):
            if p.is_file() and not str(p).startswith(str(self.sid_dir)):
                rel = str(p.relative_to(self.workdir))
                # if file is different from staged blob, report unstaged
                # naive: compare bytes to staged oid or head tree
                from hashlib import sha1
                data = p.read_bytes()
                h = sha1(data).hexdigest()
                staged_oid = staged.get(rel)
                if staged_oid and staged_oid != h:
                    changed.append(rel)
        if changed:
            print('\nModified (unstaged):')
            for c in changed:
                print('  ', c)

    def commit(self, message: str, author: Optional[str] = None) -> str:
        parent = self.head_oid()
        commit_obj = {
            'tree': self.index.as_dict(),
            'parent': parent,
            'author': author,
            'message': message,
            'timestamp': int(time.time()),
        }
        oid = self.objects.write_commit(commit_obj)
        self.update_ref(self.head_ref(), oid)
        self.index.clear()
        return oid

    def log(self, max_entries: int = 50):
        o = self.head_oid()
        while o:
            commit = self.objects.read_commit(o)
            print('commit', o)
            print('Author:', commit.get('author'))
            print('Date:', commit.get('timestamp'))
            print('\n    ' + commit.get('message') + '\n')
            o = commit.get('parent')

    def branches(self) -> List[str]:
        heads = (self.sid_dir / 'refs' / 'heads')
        return [p.name for p in heads.iterdir() if p.is_file()]

    def create_branch(self, name: str):
        head_oid = self.head_oid()
        write_ref(self.workdir, f'refs/heads/{name}', head_oid or '')

    def delete_branch(self, name: str, force: bool = False):
        ref = self.sid_dir / 'refs' / 'heads' / name
        if not ref.exists():
            raise FileNotFoundError(name)
        if not force:
            # ensure merged simple check: that branch oid is ancestor of HEAD
            branch_oid = ref.read_text().strip() or None
            head = self.head_oid()
            if branch_oid and head and branch_oid != head:
                # walk parents from head
                o = head
                found = False
                while o:
                    c = self.objects.read_commit(o)
                    if o == branch_oid:
                        found = True; break
                    o = c.get('parent')
                if not found:
                    raise RuntimeError('branch not merged; use -D to force')
        ref.unlink()

    def checkout(self, branch: str, create: bool = False):
        if create:
            self.create_branch(branch)
        # point HEAD to branch
        (self.sid_dir / 'HEAD').write_text(f'refs/heads/{branch}')
        # update worktree to branch head (naive: overwrite files from tree)
        head = self.head_oid()
        if head:
            commit = self.objects.read_commit(head)
            tree = commit.get('tree', {})
            # clear existing files (except .sid) and write files from tree blobs
            for p in self.workdir.rglob('*'):
                if p.is_file() and not str(p).startswith(str(self.sid_dir)):
                    p.unlink()
            for rel, oid in tree.items():
                data = self.objects.read_blob(oid)
                dest = self.workdir / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)

    def diff(self, staged: bool = False):
        # show diff between workdir and index (unstaged) or index and head (staged)
        import difflib
        if staged:
            left = self.index.as_dict()
            head_tree = {}
            head = self.head_oid()
            if head:
                head_tree = self.objects.read_commit(head).get('tree', {})
            pairs = [(p, head_tree.get(p), left.get(p)) for p in set(head_tree) | set(left)]
            for p, a_oid, b_oid in pairs:
                a = self.objects.read_blob(a_oid).decode() if a_oid else ''
                b = self.objects.read_blob(b_oid).decode() if b_oid else ''
                print('\n---', p)
                for line in difflib.unified_diff(a.splitlines(), b.splitlines(), fromfile='a/'+p, tofile='b/'+p, lineterm=''):
                    print(line)
        else:
            # unstaged: compare workdir file to staged blob (if any)
            for p in self.workdir.rglob('*'):
                if p.is_file() and not str(p).startswith(str(self.sid_dir)):
                    rel = str(p.relative_to(self.workdir))
                    staged = self.index.as_dict().get(rel)
                    if staged:
                        a = p.read_text()
                        b = self.objects.read_blob(staged).decode()
                        if a != b:
                            for line in difflib.unified_diff(b.splitlines(), a.splitlines(), fromfile='a/'+rel, tofile='b/'+rel, lineterm=''):
                                print(line)

    def reset(self, path: str):
        self.index.unstage(path)

    def rm(self, path: str):
        p = self.workdir / path
        if p.exists():
            p.unlink()
        self.index.unstage(path)
        # stage deletion by storing None? we'll remove from index and rely on commit tree snapshot
        # If present in index, remove
        # no explicit delete object

    # merge: simple fast-forward or create merge commit with two parents (no conflict resolution)
    def merge(self, branch: str):
        target_ref = self.sid_dir / 'refs' / 'heads' / branch
        if not target_ref.exists():
            raise FileNotFoundError(branch)
        target_oid = target_ref.read_text().strip() or None
        head = self.head_oid()
        if not target_oid:
            return
        # fast-forward if head is ancestor of target -> set HEAD to target
        # check if head is ancestor of target (walk parents)
        o = target_oid
        found = False
        while o:
            if o == head:
                found = True; break
            o = self.objects.read_commit(o).get('parent')
        if found:
            # fast-forward: set current head ref to target_oid
            self.update_ref(self.head_ref(), target_oid)
            print('Fast-forwarded')
            return
        # otherwise create merge commit with two parents
        commit_obj = {
            'tree': self.index.as_dict(),
            'parent': head,
            'parent2': target_oid,
            'author': None,
            'message': f'Merge branch {branch} into {self.head_ref()}',
            'timestamp': int(time.time())
        }
        oid = self.objects.write_commit(commit_obj)
        self.update_ref(self.head_ref(), oid)
        print('Created merge commit', oid)

    # stash: save current workdir changes (naive: snapshot all files into an object under refs/stash/<n>)
    def stash(self):
        # snapshot all files into tree mapping and store as commit-like object with message 'WIP stash'
        tree = {}
        for p in self.workdir.rglob('*'):
            if p.is_file() and not str(p).startswith(str(self.sid_dir)):
                rel = str(p.relative_to(self.workdir))
                oid = self.objects.write_blob(p.read_bytes())
                tree[rel] = oid
        commit_obj = {
            'tree': tree,
            'parent': None,
            'author': None,
            'message': 'WIP stash',
            'timestamp': int(time.time())
        }
        oid = self.objects.write_commit(commit_obj)
        # write to refs/stash list (append)
        stash_dir = self.sid_dir / 'refs' / 'stash'
        stash_dir.mkdir(parents=True, exist_ok=True)
        # use numeric filenames
        i = 0
        while (stash_dir / str(i)).exists():
            i += 1
        (stash_dir / str(i)).write_text(oid)
        print('Saved stash', i, oid)

    def stash_list(self):
        sd = self.sid_dir / 'refs' / 'stash'
        if not sd.exists():
            print('No stash entries.')
            return
        for p in sorted(sd.iterdir(), key=lambda x: int(x.name)):
            print(p.name, p.read_text().strip())

    def stash_pop(self):
        sd = self.sid_dir / 'refs' / 'stash'
        if not sd.exists():
            print('No stash entries.')
            return
        # pop last
        items = sorted(sd.iterdir(), key=lambda x: int(x.name))
        if not items:
            print('No stash entries.'); return
        last = items[-1]
        oid = last.read_text().strip()
        commit = self.objects.read_commit(oid)
        tree = commit.get('tree', {})
        for rel, blob in tree.items():
            dest = self.workdir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(self.objects.read_blob(blob))
        last.unlink()
        print('Applied stash', last.name)

    # remotes: simple local filesystem remotes via file:///path
    def remote_add(self, name: str, url: str):
        remotes = self.sid_dir / 'refs' / 'remotes' / name
        remotes.parent.mkdir(parents=True, exist_ok=True)
        remotes.write_text(url)

    def remote_list(self):
        rem_dir = self.sid_dir / 'refs' / 'remotes'
        if not rem_dir.exists():
            print('No remotes')
            return
        for p in rem_dir.iterdir():
            print(p.name, p.read_text().strip())

    def fetch(self, remote: str):
        # only support file:///path
        rem_dir = self.sid_dir / 'refs' / 'remotes' / remote
        if not rem_dir.exists(): raise FileNotFoundError(remote)
        url = rem_dir.read_text().strip()
        if not url.startswith('file://'): raise RuntimeError('only file:// remotes supported')
        path = Path(url[len('file://'):]).resolve()
        # copy objects and refs (naive)
        src = path / '.sid'
        if not src.exists(): raise FileNotFoundError('remote .sid not found')
        # copy objects
        src_objects = src / 'objects'
        dst_objects = self.sid_dir / 'objects'
        dst_objects.mkdir(parents=True, exist_ok=True)
        for f in src_objects.iterdir():
            dst = dst_objects / f.name
            if not dst.exists():
                dst.write_bytes(f.read_bytes())
        # copy refs under refs/heads/remote/*
        src_heads = src / 'refs' / 'heads'
        dst_heads = self.sid_dir / 'refs' / 'remotes' / remote / 'heads'
        dst_heads.parent.mkdir(parents=True, exist_ok=True)
        for f in src_heads.iterdir():
            dstf = dst_heads / f.name
            dstf.write_text(f.read_text())
        print('Fetched from', remote)

    def push(self, remote: str, branch: str):
        rem_dir = self.sid_dir / 'refs' / 'remotes' / remote
        if not rem_dir.exists(): raise FileNotFoundError(remote)
        url = rem_dir.read_text().strip()
        if not url.startswith('file://'): raise RuntimeError('only file:// remotes supported')
        path = Path(url[len('file://'):]).resolve()
        dst_sid = path / '.sid'
        dst_sid.mkdir(parents=True, exist_ok=True)
        # copy objects
        for f in (self.sid_dir / 'objects').iterdir():
            dst = dst_sid / 'objects' / f.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                dst.write_bytes(f.read_bytes())
        # update remote head for branch
        src_ref = self.sid_dir / 'refs' / 'heads' / branch
        if not src_ref.exists(): raise FileNotFoundError(branch)
        dst_ref = dst_sid / 'refs' / 'heads' / branch
        dst_ref.parent.mkdir(parents=True, exist_ok=True)
        dst_ref.write_text(src_ref.read_text())
        print('Pushed', branch, 'to', remote)

    def pull(self, remote: str, branch: str):
        # fetch then merge fast-forward or create merge commit
        self.fetch(remote)
        # remote head stored under refs/remotes/<remote>/heads/<branch>
        remote_head = self.sid_dir / 'refs' / 'remotes' / remote / 'heads' / branch
        if not remote_head.exists(): raise FileNotFoundError('remote branch not found')
        remote_oid = remote_head.read_text().strip() or None
        if not remote_oid: return
        head = self.head_oid()
        # if head is ancestor of remote_oid fast-forward to remote_oid
        o = remote_oid
        found = False
        while o:
            if o == head:
                found = True; break
            o = self.objects.read_commit(o).get('parent')
        if found:
            self.update_ref(self.head_ref(), remote_oid)
            print('Fast-forwarded to remote')
        else:
            # merge
            commit_obj = {
                'tree': self.index.as_dict(),
                'parent': head,
                'parent2': remote_oid,
                'author': None,
                'message': f'Merge remote {remote}/{branch}',
                'timestamp': int(time.time())
            }
            oid = self.objects.write_commit(commit_obj)
            self.update_ref(self.head_ref(), oid)
            print('Created merge commit', oid)
