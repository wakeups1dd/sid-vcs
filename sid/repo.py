import os

def init(path='.'):
    sid_path = os.path.join(path, '.sid')
    if os.path.exists(sid_path):
        print("Repository already initialized.")
        return
    os.makedirs(os.path.join(sid_path, 'objects'))
    open(os.path.join(sid_path, 'index'), 'w').close()
    open(os.path.join(sid_path, 'HEAD'), 'w').close()
    print("Initialized empty SID repository.")
