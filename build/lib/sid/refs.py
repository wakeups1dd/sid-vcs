from pathlib import Path
from typing import Optional

SID_DIR = '.sid'

def refs_dir(repo_path: Path) -> Path:
    return repo_path / SID_DIR / 'refs'

def read_ref(repo_path: Path, ref: str) -> Optional[str]:
    p = repo_path / SID_DIR / ref
    if p.exists():
        return p.read_text().strip() or None
    return None

def write_ref(repo_path: Path, ref: str, oid: str):
    p = repo_path / SID_DIR / ref
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(oid or '')

