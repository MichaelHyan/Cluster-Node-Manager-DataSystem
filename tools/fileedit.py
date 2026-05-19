import os,base64,shutil,subprocess
SIZE_LIMIT = 1

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

def read(path,len = 0):
    try:
        file_size = os.path.getsize(path)
        if len != 0:
            lines = ''
            with open(path, 'r', encoding='utf-8') as file:
                for i in range(len):
                    line = file.readline()
                    if not line:
                        break
                    lines += f'{line}'
            return lines
        else:
            if file_size > SIZE_LIMIT * 1024 * 1024:
                return f'[A] 文件过大 ({file_size} bytes)，超过{SIZE_LIMIT}MB限制，无法读取'
            with open(path, 'r', encoding = 'utf-8') as f:
                return f.read()
    except Exception as e:
        return str(e)

def write(path, content):
    try:
        '''
        content_size = len(content.encode('utf-8'))
        if content_size > SIZE_LIMIT * 1024 * 1024:
            return f'[A] 内容过大 ({content_size} bytes)，超过{SIZE_LIMIT}MB限制，无法写入'
        '''
        with open(path, 'w', encoding = 'utf-8') as f:
            f.write(content)
        return '[A] write complete'
    except Exception as e:
        return str(e)

def delete(path):
    try:
        if os.path.isdir(path):
            os.rmdir(path)
        elif os.path.isfile(path):
            os.remove(path)
        return '[A] delete complete'
    except Exception as e:
        return str(e)

def encode(path,prex=''):
    with open(path, "rb") as file:
        return f'{prex}{base64.b64encode(file.read()).decode("utf-8")}'

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
import os

def list_dir(path):
    response = ''
    response += f"[DIR] {path}\n"
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                response += f" - [DIR] {entry.name}" if entry.is_dir() else f" - [FILE] {entry.name}\n"
    except PermissionError:
        pass
    for dirpath, dirnames, filenames in os.walk(path):
        if dirpath == path:
            continue
        response += f"[DIR] {dirpath}"
        for dirname in dirnames:
            response += f" - [FILE] {dirname}"
        for filename in filenames:
            response += f" - [FILE] {filename}"
    return response
