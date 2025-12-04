"""Staging index mapping paths -> blob oids (JSON file)
"""
import json
from pathlib import Path
from typing import Dict

SID_DIR = '.sid'

class Index:
    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.index_file = repo_path / SID_DIR / 'index'
        self._data: Dict[str, str] = {}
        self._load()

    def _load(self):
        if self.index_file.exists():
            try:
                self._data = json.loads(self.index_file.read_text())
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        self.index_file.parent.mkdir(parents=True, exist_ok=True)
        self.index_file.write_text(json.dumps(self._data, indent=2, sort_keys=True))

    def stage(self, path: str, oid: str):
        self._data[path] = oid
        self._save()

    def unstage(self, path: str):
        if path in self._data:
            del self._data[path]
            self._save()

    def clear(self):
        self._data = {}
        self._save()

    def items(self):
        return list(self._data.items())

    def as_dict(self):
        return dict(self._data)
