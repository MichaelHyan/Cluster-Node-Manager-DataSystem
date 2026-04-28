from tools import fileedit,runcmd,webgrab,timer
from prompt_loader import prompt
import bot
import copy,json,time,threading,os
enable_log = True

if not os.path.exists('./files'):
    os.makedirs('./files')
if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./bak'):
    os.makedirs('./bak')

class CNMD():
    def __init__(self,prompt = prompt):
        with open('config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        self.TIME_STAMP = round(time.time())
        self.stage_break = self.config['break']
        self.prompt = prompt.load('Agent')
        self.msg_stack = []
        self.nodelist = {}
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.allow_reasoning = False
        self.allow_cmd = []
        self.help_text = '''可用命令：
1. 节点操作 (#node)
#node save <节点名称>      - 保存当前对话状态到指定节点
#node load <节点名称>      - 从指定节点加载对话状态
#node list                - 列出所有已保存的节点
#node backward <轮数>     - 回退指定轮数的对话（默认回退1轮）
2. 系统命令
#backup                   - 备份当前工作目录
#help                     - 显示此帮助信息
3. Agent命令
#bot reasoning True/False - 开关返回思考内容
#bot reset                - 清空记录
#bot prompt               - 切换人设（测试接口）
使用示例：
#node save important_conversation
#node load important_conversation
#node backward 2
#backup

注意：
- 节点名称可以是任意字符串，用于标识保存的对话状态
- backward命令用于撤销最近的对话轮次
- 备份文件会保存在备份目录中'''
    
    def user_command(self,cmd):
        cmd = cmd.split()
        if cmd[0] == '#node':
            if cmd[1] == 'save':
                self.nodelist[cmd[2]] = copy.deepcopy(self.msg)
                self.msg_stack.append(f'[D] [{cmd[2]}] save complete')
            elif cmd[1] == 'load':
                temp = self.nodelist.get(cmd[2])
                if temp:
                    self.msg = copy.deepcopy(self.nodelist.get(cmd[2]))
                    self.msg_stack.append('[D] load complete')
                else:
                    self.msg_stack.append('[D] node not found')
            elif cmd[1] == 'loadf':
                temp = self.nodelist.get(cmd[2])
                if temp:
                    try:
                        with open(f'./logs/{temp}.json','r',encoding='utf-8') as f:
                            self.messages = json.load(f)
                        with open(f'./logs/{temp}_node.json','r',encoding='utf-8') as f:
                            self.nodelist = json.load(f)
                        self.msg_stack.append('[D] load complete')
                    except:
                        self.msg_stack.append('[D] file not found')
                else:
                    self.msg_stack.append('[D] load failed')
            elif cmd[1] == 'list':
                temp = f'[D] node list:\n'
                for key,value in self.nodelist.items():
                    temp += f'{key} {value}\n'
                self.msg_stack.append(temp.strip())
            elif cmd[1] == 'backward':
                if len(self.msg) == 1:
                    self.msg_stack.append('[D] unable to backward')
                self.nodelist['temp'] = copy.deepcopy(self.msg)
                try:
                    self.msg = self.msg[:-2*int(cmd[2])]
                    self.msg_stack.append(f'[D] backward {cmd[2]} complete')
                except:
                    self.msg = self.msg[:-2]
                    self.msg_stack.append('[D] backward complete')
            else:
                self.msg_stack.append('[D] command not found')
        elif cmd[0] == '#help':
            self.msg_stack.append(self.help_text)
            return
        elif cmd[0] == '#bot':
            if cmd[1] == 'reasoning':
                if cmd[2] == 'on' or cmd[2] == 'true' or cmd[2] == 'True' or cmd[2] == '1':
                    self.allow_reasoning = True
                    self.msg_stack.append('[D] bot reasoning on')
                elif cmd[2] == 'off' or cmd[2] == 'false' or cmd[2] == 'False' or cmd[2] == '0':
                    self.allow_reasoning = False
                    self.msg_stack.append('[D] bot reasoning off')
                else:
                    self.msg_stack.append('[D] command not found')
                    return
            elif cmd[1] == 'prompt':
                self.set_prompt(cmd[2])
            elif cmd[1] == 'reset':
                self.reset()
                return
            else:
                self.msg_stack.append('[D] command not found')
                return
        elif cmd[0] == '#backup':
            fileedit.backup(self.config['base_path'])
            self.msg_stack.append('[D] backup created')
            return
        else:
            self.msg_stack.append('[D] command not found')
            return
    
    def reset(self):
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.msg_stack.append('[D] bot reset')

    def set_prompt(self,p):
        self.prompt = prompt.load(p)
        self.TIME_STAMP = round(time.time())
        self.nodelist = {}
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.msg_stack.append('[D] bot prompt set')

    def CNMD(self,cmd):
        cmd_check = ''
        if cmd[0] == '#':
            self.user_command(cmd)
            return
        while True:
            if cmd[:3] == '#I#':
                self.messages.append(
                    {
                        "role":"user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{cmd[3:]}"
                                }
                            },
                            {
                                "type": "text",
                                "text": "已读取图片"
                            }
                        ]
                    }
                )
            elif cmd[:3] == '#A#':
                self.messages.append(
                    {
                        "role":"user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": cmd[3:],
                                    "format": "mp3"
                                }
                            },
                            {
                                "type": "text",
                                "text": "已读取音频"
                            }
                        ]
                    }
                )
            elif cmd[:3] == '#V#':
                self.messages.append(
                    {
                        "role":"user",
                        "content": [
                            {
                                "type": "video_url",
                                "video_url": {
                                    "url": cmd[3:],
                                    "format": "mp4",
                                    "fps": 2,
                                    "media_resolution": "default"
                                }
                            },
                            {
                                "type": "text",
                                "text": "已读取图片"
                            }
                        ]
                    }
                )
            else:
                self.messages.append(
                    {
                        "role":"user",
                        "content": cmd
                    }
                )
            self.msg.append(self.tic)
            self.tic += 1
            post = []
            for i in self.msg:
                post.append(self.messages[i])
            response = bot.reply(post)
            #response = {'content':input('>>>'),'reasoning_content':'bruhhhh'}#bruhlang-debugger
            #response = {'content':f'bruh!!!','reasoning_content':'bruhhhh'}
            if response:
                content = response.get('content')
                reasoning_content = response.get('reasoning_content')
                if reasoning_content and self.allow_reasoning:
                    self.msg_stack.append(f'reasoning: {reasoning_content}')
            else:
                content = '[D] response failed'
                reasoning_content = '[D] response failed'
            if '$$$' not in content:
                if content == '':
                    self.msg_stack.append('[D] response failed, try again.')
                else:
                    self.msg_stack.append(content)
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                with open(f'./logs/{self.TIME_STAMP}.json','w',encoding='utf-8') as f:
                    json.dump(self.messages,f,indent=4,ensure_ascii=False)
                with open(f'./logs/{self.TIME_STAMP}_node.json','w',encoding='utf-8') as f:
                    json.dump(self.nodelist,f,indent=4,ensure_ascii=False)
                break
            else:
                self.msg_stack.append(content.split('$$$')[0])
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                sys_cmd = content.split('$$$')[1]
                if enable_log:
                    with open(f'./logs/{self.TIME_STAMP}.json','w',encoding='utf-8') as f:
                        json.dump(self.messages,f,indent=4,ensure_ascii=False)
                try:
                    if cmd_check == sys_cmd:
                        if self.stage_break:
                            self.msg_stack.append(f'[D] command refused, stage terminated')
                            break
                        else:
                            self.msg_stack.append(f'[D] command refused')
                            cmd = 'Agent已驳回重复指令，进行下一项任务。'
                    else:
                        cmd_check = copy.deepcopy(sys_cmd)
                        sys_cmd = sys_cmd.split(' ',maxsplit=2)
                        if sys_cmd[0] in self.allow_cmd:#外部指令
                            self.msg_stack.append(content)
                            break
                        if sys_cmd[0] == 'dir':
                            path = sys_cmd[1]
                            cmd = fileedit.dir(path)
                            self.msg_stack.append(f'[D] command [dir] excuted')
                        elif sys_cmd[0] == 'listdir':
                            path = sys_cmd[1]
                            cmd = fileedit.list_dir(path)
                            self.msg_stack.append(f'[D] command [listdir] excuted')
                        elif sys_cmd[0] == 'read':
                            path = sys_cmd[1]
                            cmd = fileedit.read(path)
                            self.msg_stack.append(f'[D] command [read] [{path}] excuted')
                        elif sys_cmd[0] == 'write':
                            path = sys_cmd[1]
                            content = sys_cmd[2]
                            cmd = fileedit.write(path,content)
                            self.msg_stack.append(f'[D] command [write] [{path}] excuted')
                        elif sys_cmd[0] == 'delete':
                            path = sys_cmd[1]
                            cmd = fileedit.delete(path)
                            self.msg_stack.append(f'[D] command [delete] [{path}] excuted')
                        elif sys_cmd[0] == 'time':
                            cmd = timer.timer()
                            self.msg_stack.append(f'[D] command [time] excuted')
                        elif sys_cmd[0] == 'imread':
                            path = sys_cmd[1]
                            cmd = fileedit.encode(path,'#I#')
                            self.msg_stack.append(f'[D] command [image read] [{path}] excuted')
                        elif sys_cmd[0] == 'auread':
                            path = sys_cmd[1]
                            cmd = fileedit.encode(path,'#A#')
                            self.msg_stack.append(f'[D] command [audio read] [{path}] excuted')
                        elif sys_cmd[0] == 'viread':
                            path = sys_cmd[1]
                            cmd = fileedit.encode(path,'#V#')
                            self.msg_stack.append(f'[D] command [video read] [{path}] excuted')
                        elif sys_cmd[0] == 'web':
                            if sys_cmd[1] == 'grab':
                                cmd = webgrab.get_html(sys_cmd[2])
                                self.msg_stack.append(f'[D] command [webgrab] [{sys_cmd[2]}] excuted')
                            if sys_cmd[1] == 'setheader':
                                header = json.loads(sys_cmd[2])
                                webgrab.headers = header
                                cmd = f'web header set {header}'
                                self.msg_stack.append(f'[D] command [webgetheader] [{header}] excuted')
                            if sys_cmd[1] == 'ping':
                                cmd = webgrab.ping(sys_cmd[2])
                                self.msg_stack.append(f'[D] command [ping] [{sys_cmd[2]}] excuted')
                        elif sys_cmd[0] == 'cmd':
                            if sys_cmd[1] == '-i':
                                runcmd.cmd_output=''
                                runcmd.cmd(sys_cmd[2].split())
                                self.msg_stack.append(f'[D] command [{sys_cmd[2]}] excuted')
                                time.sleep(5)
                                cmd = copy.deepcopy(runcmd.cmd_output)
                            elif sys_cmd[1] == '-w':
                                runcmd.cmd_output=''
                                t = threading.Thread(target=runcmd.cmd, args=(sys_cmd[2].split(' '),))
                                t.start()
                                cmd = 'command excuted'
                                self.msg_stack.append(f'[D] command [{sys_cmd[2]}] excuted')
                            elif sys_cmd[1] == '-o':
                                cmd = copy.deepcopy(runcmd.cmd_output)
                                self.msg_stack.append(f'[D] command [cmd output] excuted')
                        else:
                            cmd = 'command not found'
                except Exception as e:
                    cmd = str(e)
        return

def stack_print(stack):
    while True:
        if stack:
            item = stack.pop(0)
            print(item)
        time.sleep(0.5)
if __name__ == '__main__':
    CNM = CNMD()
    t = threading.Thread(target=stack_print,args=(CNM.msg_stack,),daemon=True)
    t.start()
    while True:
        cmd = input('=======================================================================\n')
        CNM.CNMD(cmd)