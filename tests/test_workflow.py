import os, shutil
from pathlib import Path
from sid.cli import main

def run(cmd, cwd):
    old = os.getcwd()
    try:
        os.chdir(cwd)
        parts = cmd.split()
        return main(parts)
    finally:
        os.chdir(old)

def test_init_add_commit(tmp_path):
    p = tmp_path/'repo'
    p.mkdir()
    assert run('init', p) == 0
    (p/'file.txt').write_text('hello')
    assert run('add file.txt', p) == 0
    assert run('commit -m init', p) == 0
    assert (p/'.sid').exists()

def test_branch_checkout_merge(tmp_path):
    p = tmp_path/'repo2'
    p.mkdir()
    assert run('init', p) == 0
    (p/'a.txt').write_text('a')
    assert run('add a.txt', p) == 0
    assert run('commit -m base', p) == 0
    assert run('branch feature', p) == 0
    assert run('checkout -b feature', p) == 0
    (p/'a.txt').write_text('feature change')
    assert run('add a.txt', p) == 0
    assert run('commit -m feat', p) == 0
    assert run('checkout master', p) == 0
    # merge feature into master (creates merge commit or fast-forward)
    assert run('merge feature', p) == 0

def test_stash(tmp_path):
    p = tmp_path/'repo3'
    p.mkdir()
    assert run('init', p) == 0
    (p/'x.txt').write_text('1')
    assert run('add x.txt', p) == 0
    assert run('commit -m c', p) == 0
    # modify and stash
    (p/'x.txt').write_text('2')
    assert run('stash', p) == 0
    assert run('stash list', p) == 0
    assert run('stash pop', p) == 0
