import sys
from .repo import init
from .index import add_to_index
from .objects import create_commit, show_log

def main():
    if len(sys.argv) < 2:
        print("Usage: sid <command>")
        return

    cmd = sys.argv[1]

    if cmd == "init":
        init()
    elif cmd == "add":
        file = sys.argv[2]
        add_to_index(file)
    elif cmd == "commit":
        message = sys.argv[2]
        files = open(".sid/index").read().splitlines()
        create_commit(message, files)
        open(".sid/index", "w").close()
    elif cmd == "log":
        show_log()
    else:
        print(f"Unknown command: {cmd}")
