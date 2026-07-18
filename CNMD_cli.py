import CNMD
import threading, time, copy, os, argparse
from tools.color_utils import (
    Color, print_color, print_success, print_warning, 
    print_error, print_info, color_text
)

input_list = ''
parser = argparse.ArgumentParser()
parser.add_argument('name', nargs='?', default='agent_cli')
args = parser.parse_args()

cnm = CNMD.CNMD()
cnm.set_prompt(args.name)

#DIVIDER = f'{Color.DIM}{'─' * 44}{Color.RESET}'
DIVIDER = f'{Color.WHITE}{'─' * 44}{Color.RESET}'

def print_banner():
    print()
    print(f'{Color.CYAN}{Color.BRIGHT}')
    print(r"╭──────────────────────────────────────────╮")
    print(r"│     ___                          ___     |")
    print(r"│   //   \\ |\\  || |\\  |\\  || ||   \\   |")
    print(r"│  ||       ||\\ || ||\\ ||\\ || ||   ||   |")
    print(r"│  ||       || \\|| || \\|| \\|| ||   ||   |")
    print(r"│   \\___// ||  \|| ||  \||  \|| ||___//   |")
    print(r"│  ===Cluster Node Manager DataSystem====  |")
    print(r"╰──────────────────────────────────────────╯")
    print(f"{Color.RESET}")
    print(DIVIDER)

def input_thread():
    global input_list, cnm
    while True:
        try:
            print("\033[97m", end='', flush=True)
            user_input = input()
            print("\033[0m", end='', flush=True)
            
            if user_input == '' and input_list != '':
                threading.Thread(target=agent_thread).start()
                print(DIVIDER)
            elif user_input == '#pause':
                cnm.mslock = False
            elif user_input == '#exit':
                print(DIVIDER)
                os._exit(0)
            elif user_input == '' and input_list == '':
                pass
            else:
                input_list += user_input
        except Exception as e:
            print_error(f"✗ {e}")
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
            if cnm.msg_stack:
                pass
            else:
                print(f"{Color.MAGENTA}●{Color.RESET} {Color.CYAN}Assistant{Color.RESET}")
            print(f"{first_element}")
            if not cnm.msg_stack:
                print(DIVIDER)
        time.sleep(0.1)

if __name__ == "__main__":
    print_banner()
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