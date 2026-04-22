import subprocess
import threading
import time

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

if __name__ == "__main__":
    cmd_input = ['python','D:/git/Cluster-Node-Manager-DataSystem/test.py']
    t = threading.Thread(target=cmd, args=(cmd_input,))
    t.start()
    time.sleep(1)
    print(cmd_output)

