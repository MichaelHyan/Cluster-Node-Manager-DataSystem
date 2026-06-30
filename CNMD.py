from tools import fileedit,memory
from prompt_loader import prompt
import tool_handler as tool
import tools.bot as bot
import tools.lang as lang
import copy,json,time,threading,os
enable_log = True

if not os.path.exists('./files'):
    os.makedirs('./files')
if not os.path.exists('./logs'):
    os.makedirs('./logs')
if not os.path.exists('./bak'):
    os.makedirs('./bak')
print(r'''
    ___                                ___
  //   \\ ||\\   || ||\\   ||\\   || ||   \\
 ||       || \\  || || \\  || \\  || ||   ||
 ||       ||  \\ || ||  \\ ||  \\ || ||   ||
  \\___// ||   \\|| ||   \\||   \\|| ||___//
======Cluster Node Manager DataSystem=======
''')

USR_COMMAND = [
    '#help',
    '#node save',
    '#node load',
    '#node list',
    '#node backward',
    '#node backwardms',
    '#backup',
    '#help',
    '#bot reasoning',
    '#bot reset',
    '#bot reload'
    '#bot prompt',
    '#mem save',
    '#mem analyse'
    ]

class CNMD():
    def __init__(self,prompt = prompt):
        with open('config.json',encoding='utf-8') as f:
            self.config = json.load(f)
        self.TIME_STAMP = round(time.time())
        self.stage_break = self.config['break']
        self.prompt = prompt.load('agent_base')
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
        self.mslock = True
        self.mstemp = []
        
        self.mission = []
        self.is_mission = False

        self.help_text = '''可用命令：
1. 节点操作 (#node)
#node save <节点名称>      - 保存当前对话状态到指定节点
#node load <节点名称>      - 从内存中加载指定节点的对话状态
#node list                - 列出所有已保存的节点
#node backward <轮数>     - 回退指定轮数的对话（默认回退1轮）
#node backwardms          - 回退一次事件操作

2. 系统命令
#backup                   - 备份当前工作目录
#help                     - 显示此帮助信息

3. Agent命令
#bot reasoning <状态>     - 开关返回思考内容 (状态可选: on/true/True/1 或 off/false/False/0)
#bot reset                - 清空对话记录
#bot reload               - 重载模型参数
#bot prompt <人设名>      - 切换人设（测试接口）

4. 记忆能力
#mem save                 - 总结记忆
#mem analyse              - 整理记忆'''

    def _similarity(self,str1, str2):
        set1 = set(str1)
        set2 = set(str2)
        intersection = set1 & set2
        union = set1 | set2
        if not union:
            return 1.0 if not intersection else 0.0
        return len(intersection) / len(union)

    def _correction(self,str):
        s = {}
        for i in USR_COMMAND:
            s[i] = self._similarity(str,i)
        self.msg_stack.append(f'{lang.lang['cnmd.base.notfound']}{max(s,key=s.get)}')

    def _compress_number(self,nums):
        result = []
        start = nums[0]
        for i in range(1, len(nums)):
            if nums[i] != nums[i-1] + 1:
                end = nums[i-1]
                if start == end:
                    result.append(str(start))
                else:
                    result.append(f"{start}-{end}")
                start = nums[i]
        if start == nums[-1]:
            result.append(str(start))
        else:
            result.append(f"{start}-{nums[-1]}")
        return ",".join(result)
    
    def _user_command(self,cmd):
        ori_cmd = copy.deepcopy(cmd)
        cmd = cmd.split()
        if cmd[0] == '#node':
            if cmd[1] == 'save':
                self.nodelist[cmd[2]] = copy.deepcopy(self.msg)
                self.msg_stack.append(f'{lang.lang['cnmd.node.savecomplete']}{cmd[2]}')
            elif cmd[1] == 'load':
                temp = self.nodelist.get(cmd[2])
                if temp:
                    self.msg = copy.deepcopy(self.nodelist.get(cmd[2]))
                    self.msg_stack.append(f'{lang.lang['cnmd.node.loadcomplete']}{cmd[2]}')
                else:
                    self.msg_stack.append(f'{lang.lang['cnmd.node.nodenotfound']}')
            elif cmd[1] == 'loadf':
                temp = cmd[2]
                if temp:
                    try:
                        with open(f'./logs/{temp}.json','r',encoding='utf-8') as f:
                            self.messages = json.load(f)
                        with open(f'./logs/{temp}_node.json','r',encoding='utf-8') as f:
                            self.nodelist = json.load(f)
                        self.msg_stack.append(lang.lang['cnmd.log.loadcomplete'])
                    except Exception as e:
                        self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
                else:
                    self.msg_stack.append(lang.lang['cnmd.log.filenotfound'])
            elif cmd[1] == 'list':
                temp = f'{lang.lang['cnmd.node.nodelist']}\n'
                for key,value in self.nodelist.items():
                    temp += f'{key} [{self._compress_number(value)}]\n'
                self.msg_stack.append(temp.strip())
            elif cmd[1] == 'backward':
                if len(self.msg) == 1:
                    self.msg_stack.append(lang.lang['cnmd.node.backwardunable'])
                self.nodelist['temp'] = copy.deepcopy(self.msg)
                try:
                    self.msg = self.msg[:-2*int(cmd[2])]
                    self.msg_stack.append(f'{lang.lang['cnmd.node.backwardcount']}{cmd[2]}')
                except:
                    self.msg = self.msg[:-2]
                    self.msg_stack.append(lang.lang['cnmd.node.backward'])
            elif cmd[1] == 'backwardms':
                self.msg = copy.deepcopy(self.mstemp)
                self.msg_stack.append(lang.lang['cnmd.node.backward'])
            else:
                self._correction(ori_cmd)
        elif cmd[0] == '#help':
            self.msg_stack.append(self.help_text)
        elif cmd[0] == '#bot':
            if cmd[1] == 'reasoning':
                if cmd[2] == 'on' or cmd[2] == 'true' or cmd[2] == 'True' or cmd[2] == '1':
                    self.allow_reasoning = True
                    self.msg_stack.append(lang.lang['cnmd.bot.reasoningon'])
                elif cmd[2] == 'off' or cmd[2] == 'false' or cmd[2] == 'False' or cmd[2] == '0':
                    self.allow_reasoning = False
                    self.msg_stack.append(lang.lang['cnmd.bot.reasoningoff'])
                else:
                    self._correction(ori_cmd)
            elif cmd[1] == 'prompt':
                self.set_prompt(cmd[2])
            elif cmd[1] == 'reset':
                self._reset()
            elif cmd[1] == 'reload':
                bot.reload()
                self.msg_stack.append(lang.lang['cnmd.bot.reload'])
            else:
                self._correction(ori_cmd)
        elif cmd[0] == '#backup':
            fileedit.backup(self.config['base_path'])
            self.msg_stack.append(lang.lang['cnmd.base.backup'])
        elif cmd[0] == '#mem':
            if cmd[1] == 'save':
                post = []
                for i in self.msg:
                    post.append(self.messages[i])
                memory.save(post)
                self.msg_stack.append(lang.lang['cnmd.mem.save'])
            elif cmd[1] == 'analyse':
                memory.analyse()
                self.msg_stack.append(lang.lang['cnmd.mem.analyse'])
            else:
                self._correction(ori_cmd)
        else:
            self._correction(ori_cmd)
    
    def _system_command(self,sys_cmd,ori_cmd):
        if sys_cmd[0] == 'pass':
            cmd = lang.lang['bot.base.missionpass']
        elif sys_cmd[0] == 'msm':
            sys_cmd = sys_cmd[1].split(' ',maxsplit=1)
            if sys_cmd[0] == 'set':
                m = sys_cmd[1].split('#')
                for i in m:
                    if m != '':
                        self.mission.append(i)
                cmd = lang.lang['bot.agentlog.setmission']
                self.msg_stack.append(lang.lang['bot.agentlog.setmission'])
            elif sys_cmd[0] == 'start':
                self.is_mission = True
                temp_nodelist = copy.deepcopy(self.nodelist)
                temp_msg = copy.deepcopy(self.msg)
                temp_messages = copy.deepcopy(self.messages)
                temp_tic = copy.deepcopy(self.tic)
                self._mission_init()
                self.msg_stack.append(lang.lang['bot.agentlog.runmission'])
        elif sys_cmd[0] == 'quit':#msm
            if len(self.mission) != 0:
                self.msg_stack.append(lang.lang['bot.agentlog.quitmission'])
                self._mission_init()
            else:
                self.is_mission = False
                self.messages = copy.deepcopy(temp_messages)
                self.nodelist = copy.deepcopy(temp_nodelist)
                self.msg = copy.deepcopy(temp_msg)
                self.tic = copy.deepcopy(temp_tic)
                self.TIME_STAMP = round(time.time())
                cmd = lang.lang['bot.tool.missiondone']
        else:
            toolcall = tool.tool(ori_cmd)
            cmd = toolcall['sys']
            self.msg_stack.append(toolcall['cli'])
        return cmd
    
    def _reset(self):
        self.TIME_STAMP = round(time.time())
        self.nodelist['init'] = [0]
        self.messages = [
            {
                "role":"system",
                "content":self.prompt
            }
        ]
        self.msg = self.nodelist['init']
        self.tic = 1
        self.msg_stack.append(lang.lang['cnmd.bot.reset'])

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
        self.msg_stack.append(lang.lang['cnmd.bot.setprompt'])

    def _mission_init(self):
        self.prompt = prompt.load('msm')
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
        self.msg_stack.append(lang.lang['bot.agentlog.submission'])

    def CNMD(self,cmd):
        cmd_check = ''
        if cmd[0] == '#' and not self.is_mission:
            self._user_command(cmd)
            return
        self.mstemp = copy.deepcopy(self.msg)
        while True and self.mslock:
            if self.is_mission and len(self.mission) != 0:
                cmd = self.mission.pop()
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
                                "text": lang.lang['bot.multimodel.imread']
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
                                    "format": "audio/mp3"
                                }
                            },
                            {
                                "type": "text",
                                "text": lang.lang['bot.multimodel.auread']
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
                                "text": lang.lang['bot.multimodel.viread']
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
            if response:
                content = response.get('content')
                reasoning_content = response.get('reasoning_content')
                if reasoning_content and self.allow_reasoning:
                    self.msg_stack.append(f'reasoning: {reasoning_content}')
            else:
                content = lang.lang['cnmd.bot.responsefail']
                reasoning_content = lang.lang['cnmd.bot.responsefail']
            if '$$$' not in content and not self.is_mission:
                if content == '':
                    self.msg_stack.append(lang.lang['cnmd.bot.responsefailcontinue'])
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
                if content.split('$$$')[0] != '':
                    self.msg_stack.append(content.split('$$$')[0])
                self.messages.append(
                    {
                        "role": "system",
                        "content": content
                    }
                )
                self.msg.append(self.tic)
                self.tic += 1
                try:
                    sys_cmd = content.split('$$$',maxsplit=1)[1]
                except:
                    sys_cmd = 'pass '
                if enable_log:
                    with open(f'./logs/{self.TIME_STAMP}.json','w',encoding='utf-8') as f:
                        json.dump(self.messages,f,indent=4,ensure_ascii=False)
                    with open(f'./logs/{self.TIME_STAMP}_node.json','w',encoding='utf-8') as f:
                        json.dump(self.nodelist,f,indent=4,ensure_ascii=False)
                try:
                    if cmd_check != '' and cmd_check == sys_cmd:
                        if self.stage_break and not self.is_mission:
                            self.msg_stack.append(lang.lang['cnmd.bot.refuse'])
                            break
                        else:
                            self.msg_stack.append(lang.lang['cnmd.bot.refuse'])
                            cmd = lang.lang['bot.tool.refuse']
                    else:
                        cmd_check = copy.deepcopy(sys_cmd)
                        sys_cmd = sys_cmd.split(' ',maxsplit=1)
                        if sys_cmd[0] in self.allow_cmd:
                            self.msg_stack.append(content)
                            if not self.is_mission:
                                break
                        cmd = self._system_command(sys_cmd,cmd_check)
                except Exception as e:
                    self.msg_stack.append(f'{lang.lang['cnmd.base.error']}{str(e)}')
                    cmd = f'{lang.lang['bot.base.error']}{str(e)}'
        if self.mslock == False:
            self.mslock = True
            self.msg_stack.append(lang.lang['cnmd.base.pause'])
        return

def stack_print(stack):
    while True:
        if stack:
            item = stack.pop(0)
            print(item)
        time.sleep(0.5)

if __name__ == '__main__':
    enable_log = False
    CNM = CNMD()
    t = threading.Thread(target=stack_print,args=(CNM.msg_stack,),daemon=True)
    t.start()
    while True:
        cmd = input('============================================\n')
        CNM.CNMD(cmd)