import os,base64,shutil

def dir(path):
    try:
        all_items = os.listdir(path)
        dirs = []
        files = []
        r = ''
        for item in all_items:
            full_path = os.path.join(path, item)
            if os.path.isdir(full_path):
                dirs.append(item)
            elif os.path.isfile(full_path):
                files.append(item)        
        for d in dirs:
            r += f"[DIR]{d}\n"
        for f in files:
            r += f"[FILE]{f}\n"
        return r
    except Exception as e:
        return str(e)

def read(path):
    try:
        with open(path, 'r', encoding = 'utf-8') as f:
            return f.read()
    except Exception as e:
        return str(e)

def write(path, content):
    try:
        with open(path, 'w', encoding = 'utf-8') as f:
            f.write(content)
        return 'write complete'
    except Exception as e:
        return str(e)

def delete(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        elif os.path.isfile(path):
            os.remove(path)
        return 'delete complete'
    except Exception as e:
        return str(e)

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def backup(src_dir, dst_dir='./bak/'):
    if not os.path.exists(src_dir):
        return False
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    try:
        for item in os.listdir(src_dir):
            src_path = os.path.join(src_dir, item)
            dst_path = os.path.join(dst_dir, item)
            if os.path.isdir(src_path):
                print(f"copying: {src_path} -> {dst_path}")
                if os.path.exists(dst_path):
                    backup(src_path, dst_path)
                else:
                    shutil.copytree(src_path, dst_path)
            else:
                print(f"copying: {src_path} -> {dst_path}")
                shutil.copy2(src_path, dst_path)
        return 'copy complete'
    except Exception as e:
        return str(e)
