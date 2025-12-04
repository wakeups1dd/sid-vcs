"""Object storage for blobs and commits (simple file-per-object store)"""
import hashlib, json
from pathlib import Path
from typing import Dict, Any

SID_DIR = '.sid'

class ObjectStore:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.objects_dir = repo_path / SID_DIR / 'objects'
        self.objects_dir.mkdir(parents=True, exist_ok=True)

    def _hash(self, header: bytes, data: bytes) -> str:
        h = hashlib.sha1(header + data).hexdigest()
        return h

    def write_blob(self, data: bytes) -> str:
        header = b'blob '
        oid = self._hash(header, data)
        p = self.objects_dir / oid
        if not p.exists():
            p.write_bytes(data)
        return oid

    def read_blob(self, oid: str) -> bytes:
        p = self.objects_dir / oid
        return p.read_bytes()

    def write_commit(self, obj: Dict[str, Any]) -> str:
        raw = json.dumps(obj, sort_keys=True).encode()
        header = b'commit '
        oid = self._hash(header, raw)
        p = self.objects_dir / oid
        if not p.exists():
            p.write_bytes(raw)
        return oid

    def read_commit(self, oid: str) -> Dict[str, Any]:
        raw = (self.objects_dir / oid).read_bytes()
        return json.loads(raw.decode())
