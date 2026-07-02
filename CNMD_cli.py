import CNMD
import threading,time,copy,os,argparse

input_list = ''
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_cli')
args = parser.parse_args()

cnm = CNMD.CNMD()
cnm.set_prompt(args.name)

def input_thread():
    global input_list,cnm
    while True:
        try:
            user_input = input()
            if user_input == '' and input_list != '':
                threading.Thread(target=agent_thread).start()
                print('='*38)
            elif user_input == '#pause':
                cnm.mslock = False
            elif user_input == '#exit':
                os._exit(0)
            elif user_input == '' and input_list == '':
                pass
            else:
                input_list+=user_input
        except Exception as e:
            print(e)
            pass

def agent_thread():
    global input_list
    temp = copy.deepcopy(input_list)
    input_list = ''
    cnm.CNMD(temp)

def process_thread():
    while True:
        if cnm.msg_stack:
            first_element = cnm.msg_stack.pop(0)
            print(f">{first_element}")
            if not cnm.msg_stack:
                print('='*38)
        time.sleep(0.1)

if __name__ == "__main__":
    t_input = threading.Thread(target=input_thread)
    t_input.daemon = True 
    t_process = threading.Thread(target=process_thread)
    t_process.daemon = True

    t_input.start()
    t_process.start()
    try:
        while True:
            time.sleep(1)
    except:
        pass
