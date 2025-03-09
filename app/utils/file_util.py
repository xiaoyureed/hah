import os


def clear_dir(dir_path: str):
    if not os.path.exists(dir_path):
        return
    if os.path.isfile(dir_path):
        return

    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        
        if os.path.isfile(item_path) or os.path.islink(item_path):
            os.remove(item_path)
        elif os.path.isdir(item_path):
            clear_dir(item_path)
        else:
            print(f"Unknown file type: {item_path}")