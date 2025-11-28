def add_to_index(file_path):
    with open('.sid/index', 'a') as index:
        index.write(file_path + '\n')
    print(f"Added {file_path} to staging area.")
