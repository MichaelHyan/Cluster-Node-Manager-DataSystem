import time

def timer():
    return f'timestamp: {round(time.time())}\ntimestring: {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}\n'
