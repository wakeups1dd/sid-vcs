import hashlib, json, os

def hash_data(data):
    return hashlib.sha1(data).hexdigest()

def write_object(data):
    obj_hash = hash_data(data)
    path = f".sid/objects/{obj_hash}"
    with open(path, "wb") as f:
        f.write(data)
    return obj_hash

def create_commit(message, files):
    commit_data = json.dumps({"message": message, "files": files}).encode()
    commit_hash = write_object(commit_data)
    with open(".sid/HEAD", "w") as f:
        f.write(commit_hash)
    print(f"Committed as {commit_hash[:7]}")

def show_log():
    head = open(".sid/HEAD").read().strip()
    if not head:
        print("No commits yet.")
        return
    print("Commit:", head)
    data = open(f".sid/objects/{head}", "rb").read()
    print(data.decode())
