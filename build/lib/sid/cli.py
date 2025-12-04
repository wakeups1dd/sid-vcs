"""Command-line interface for sid"""
import argparse, sys
from pathlib import Path
from .repo import Repo

def main(argv=None):
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser(prog='sid')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('init')
    sub.add_parser('status')

    p_add = sub.add_parser('add'); p_add.add_argument('path', nargs='?', default='.')
    p_commit = sub.add_parser('commit'); p_commit.add_argument('-m','--message', required=True)
    p_config = sub.add_parser('config'); p_config.add_argument('--name'); p_config.add_argument('--email')

    p_log = sub.add_parser('log')

    p_branch = sub.add_parser('branch'); p_branch.add_argument('name', nargs='?')
    p_checkout = sub.add_parser('checkout'); p_checkout.add_argument('-b', action='store_true', dest='create'); p_checkout.add_argument('name')

    p_merge = sub.add_parser('merge'); p_merge.add_argument('branch')

    p_diff = sub.add_parser('diff'); p_diff.add_argument('--staged', action='store_true')

    p_reset = sub.add_parser('reset'); p_reset.add_argument('path')

    p_rm = sub.add_parser('rm'); p_rm.add_argument('path')

    p_stash = sub.add_parser('stash'); p_stash.add_argument('action', nargs='?', choices=['list','pop'], default='save')

    p_remote = sub.add_parser('remote'); p_remote.add_argument('action', nargs='?', choices=['add','list'], default='list'); p_remote.add_argument('name', nargs='?'); p_remote.add_argument('url', nargs='?')

    p_fetch = sub.add_parser('fetch'); p_fetch.add_argument('remote')
    p_push = sub.add_parser('push'); p_push.add_argument('remote'); p_push.add_argument('branch')
    p_pull = sub.add_parser('pull'); p_pull.add_argument('remote'); p_pull.add_argument('branch')

    args = parser.parse_args(argv)
    repo = Repo('.')

    if args.cmd == 'init':
        repo.init(); return 0
    if args.cmd == 'status':
        repo.status(); return 0
    if args.cmd == 'add':
        repo.add(args.path); return 0
    if args.cmd == 'commit':
        cfg = repo.get_config().get('user', {})
        author = f"{cfg.get('name','')} <{cfg.get('email','')}>"
        oid = repo.commit(args.message, author=author); print('Committed', oid); return 0
    if args.cmd == 'config':
        if args.name: repo.set_config('name', args.name)
        if args.email: repo.set_config('email', args.email)
        print('Config updated'); return 0
    if args.cmd == 'log':
        repo.log(); return 0
    if args.cmd == 'branch':
        if args.name:
            repo.create_branch(args.name); print('Created', args.name)
        else:
            for b in repo.branches(): print(' ', b)
        return 0
    if args.cmd == 'checkout':
        repo.checkout(args.name, create=args.create); return 0
    if args.cmd == 'merge':
        repo.merge(args.branch); return 0
    if args.cmd == 'diff':
        repo.diff(staged=args.staged); return 0
    if args.cmd == 'reset':
        repo.reset(args.path); return 0
    if args.cmd == 'rm':
        repo.rm(args.path); return 0
    if args.cmd == 'stash':
        if args.action == 'list': repo.stash_list()
        elif args.action == 'pop': repo.stash_pop()
        else: repo.stash()
        return 0
    if args.cmd == 'remote':
        if args.action == 'add' and args.name and args.url: repo.remote_add(args.name, args.url); print('Remote added')
        else: repo.remote_list(); return 0
    if args.cmd == 'fetch':
        repo.fetch(args.remote); return 0
    if args.cmd == 'push':
        repo.push(args.remote, args.branch); return 0
    if args.cmd == 'pull':
        repo.pull(args.remote, args.branch); return 0

    parser.print_help(); return 2

if __name__ == '__main__':
    raise SystemExit(main())
