from tools import fileedit,runcmd
from prompt_loader import prompt0
import bot,node
import copy,json,time,threading
class CNMD():
    def __init__(self,prompt = prompt0):
        with open('config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        self.TIME_STAMP = round(time.time())
        self.stage_break = self.config['break']
        self.prompt = prompt.load()
        self.msg_stack = []
        self.nodelist = []
        self.nodelist.append(node.node())
        self.nodelist[0].id = 'init'
        self.nodelist[0].message = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist[0].message
        self.tic = 1
        self.help_text = '''可用命令：
1. 节点操作 (#node)
#node save <节点名称>      - 保存当前对话状态到指定节点
#node load <节点名称>      - 从指定节点加载对话状态
#node list                - 列出所有已保存的节点
#node backward <轮数>     - 回退指定轮数的对话（默认回退1轮）
2. 系统命令
#backup                  - 备份当前工作目录
#help                    - 显示此帮助信息

使用示例：
#node save important_conversation
#node load important_conversation
#node backward 2
#backup

注意：
- 节点名称可以是任意字符串，用于标识保存的对话状态
- backward命令用于撤销最近的对话轮次
- 备份文件会保存在备份目录中'''
        
    def CNMD(self,cmd):
        cmd_check = ''
        if cmd[0] == '#':
            cmd = cmd.split()
            if cmd[0] == '#node':
                if cmd[1] == 'save':
                    for i in self.nodelist:
                        if i.id == cmd[2]:
                            i.message = copy.deepcopy(self.msg)
                            self.msg_stack.append(f'[D] node [{i.id}] overwrite')
                            return
                    self.nodelist.append(node.node())
                    self.nodelist[-1].id = cmd[2]
                    self.nodelist[-1].message = copy.deepcopy(self.msg)
                    self.msg_stack.append(f'[D] [{cmd[2]}] save complete')
                    return
                elif cmd[1] == 'load':
                    for i in self.nodelist:
                        if i.id == cmd[2]:
                            self.msg = copy.deepcopy(i.message)
                            self.msg_stack.append('[D] load complete')
                            return
                    self.msg_stack.append('[D] node not found')
                    return
                elif cmd[1] == 'list':
                    self.msg_stack.append('[D] node list:\n' + '\n'.join([i.id for i in self.nodelist]))
                    return
                elif cmd[1] == 'backward':
                    if len(self.msg) == 1:
                        self.msg_stack.append('[D] unable to backward')
                        return
                    for i in self.nodelist:
                        if i.id == 'temp':
                            i.message = copy.deepcopy(self.msg)
                        else:
                            self.nodelist.append(node.node())
                            self.nodelist[-1].id = 'temp'
                            self.nodelist[-1].message = copy.deepcopy(self.msg)
                        try:
                            self.msg = self.msg[:-2*int(cmd[2])]
                            self.msg_stack.append(f'[D] backward {cmd[2]} complete')
                            return
                        except:
                            self.msg = self.msg[:-2]
                            self.msg_stack.append('[D] backward complete')
                            return
                else:
                    self.msg_stack.append('[D] command not found')
                    return
            elif cmd[0] == '#help':
                self.msg_stack.append(self.help_text)
                return
            elif cmd[0] == '#backup':
                fileedit.backup(self.config['base_path'])
                self.msg_stack.append('[D] backup created')
                return
            else:
                self.msg_stack.append('[D] command not found')
                return
        while True:
            if False:#此部分尚不稳定
            #if cmd[0] == '/':
                self.messages.append(
                    {
                        "role":"user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{cmd}"
                                }
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
            #response = {'content':input('>>>'),'reasoning_content':'bruhhhh'}
            if response:
                content = response.get('content')
                reasoning_content = response.get('reasoning_content')
            else:
                content = '[D] response failed'
                reasoning_content = '[D] response failed'
            if '$$$' not in content:
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
                        elif sys_cmd[0] == 'imread':
                            path = sys_cmd[1]
                            cmd = fileedit.encode_image(path)
                            self.msg_stack.append(f'[D] command [imread] [{path}] excuted')
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