import subprocess
import threading
import time,os

cmd_output = ''
def cmd(cmd):
    global cmd_output
    try:
        process = subprocess.Popen(cmd, 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE, 
                                   text=True, 
                                   encoding='gbk')
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                cmd_output += f'{output.strip()}\n'
        return_code = process.poll()
        cmd_output += f"command end, return code: {return_code}\n"
    except Exception as e:
        cmd_output += f'{e}\n'

def pws(cmd):
    global cmd_output
    powershell_path = os.path.join(os.environ.get("SYSTEMROOT", "C:\\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe")
    try:
        result = subprocess.run(
            [powershell_path, "-Command", cmd],
            check=True,
            capture_output=True,
            text=True
        )
        cmd_output += f'{result.stdout}\n'
    except Exception as e:
        cmd_output += f'{e}\n'