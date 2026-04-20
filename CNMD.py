import tools,bot,node,prompt_loader
import copy,json,time,threading
with open('config.json',encoding='utf-8') as f:
    config = json.load(f)
TIME_STAMP = round(time.time())
stage_break = config['break']
prompt = prompt_loader.load()
help_text = '''可用命令：

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
msg_stack = []
def stack_print():
    while True:
        if msg_stack:
            item = msg_stack.pop(0)
            print(item)
        time.sleep(0.5)
t = threading.Thread(target=stack_print, daemon=True)
t.start()

nodelist = []
nodelist.append(node.node())
nodelist[0].id = 'init'
nodelist[0].message = [0]
messages = [
    {
        "role":"system",
        "content":prompt
    }
]
msg = nodelist[0].message
tic = 1
def CNMD(cmd):
    global msg
    global msg_stack
    global messages
    global tic
    global nodelist
    cmd_check = ''
    if cmd[0] == '#':
        cmd = cmd.split()
        if cmd[0] == '#node':
            if cmd[1] == 'save':
                for i in nodelist:
                    if i.id == cmd[2]:
                        i.message = copy.deepcopy(msg)
                        msg_stack.append(f'[D] node [{i.id}] overwrite')
                        return f'[D] node [{i.id}] overwrite'
                nodelist.append(node.node())
                nodelist[-1].id = cmd[2]
                nodelist[-1].message = copy.deepcopy(msg)
                msg_stack.append(f'[D] [{cmd[2]}] save complete')
                return f'[c] [{cmd[2]}] save complete'
            elif cmd[1] == 'load':
                for i in nodelist:
                    if i.id == cmd[2]:
                        msg = copy.deepcopy(i.message)
                        msg_stack.append('[c] load complete')
                        return '[c] load complete'
                msg_stack.append('[D] node not found')
                return '[c] node not found'
            elif cmd[1] == 'list':
                msg_stack.append('[D] node list:\n' + '\n'.join([i.id for i in nodelist]))
                return '[c] node list:\n' + '\n'.join([i.id for i in nodelist])
            elif cmd[1] == 'backward':
                if len(msg) == 1:
                    msg_stack.append('[D] unable to backward')
                    return '[c] unable to backward'
                for i in nodelist:
                    if i.id == 'temp':
                        i.message = copy.deepcopy(msg)
                    else:
                        nodelist.append(node.node())
                        nodelist[-1].id = 'temp'
                        nodelist[-1].message = copy.deepcopy(msg)
                    try:
                        msg = msg[:-2*int(cmd[2])]
                        msg_stack.append(f'[D] backward {cmd[2]} complete')
                        return f'[c] backward {cmd[2]} complete'
                    except:
                        msg = msg[:-2]
                        msg_stack.append('[D] backward complete')
                        return '[c] backward complete'
            else:
                msg_stack.append('[D] command not found')
                return '[c] command not found'
        elif cmd[0] == '#help':
            msg_stack.append(help_text)
            return help_text
        elif cmd[0] == '#backup':
            tools.backup(config['base_path'])
            msg_stack.append('[D] backup created')
            return '[c] backup created'
        else:
            msg_stack.append('[D] command not found')
            return '[c] command not found'
    reply = ''

    while True:
        if cmd[0] == '/':
            messages.append(
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
            messages.append(
                {
                    "role":"user",
                    "content": cmd
                }
            )
        msg.append(tic)
        tic += 1
        post = []
        for i in msg:
            post.append(messages[i])
        response = bot.reply(post)
        #response = {'content':input('<:>'),'reasoning_content':'bruhhhh'}

        if response:
            content = response.get('content')
            reasoning_content = response.get('reasoning_content')
        else:
            content = '[c] response failed'
            reasoning_content = '[c] response failed'
        if '$$$' not in content:
            msg_stack.append(content)
            messages.append(
                {
                    "role": "system",
                    "content": content
                }
            )
            reply += f'reasoning:\n{reasoning_content}\ncontext:\n{content}'
            msg.append(tic)
            tic += 1
            with open(f'./logs/{TIME_STAMP}.json','w',encoding='utf-8') as f:
                json.dump(messages,f,indent=4,ensure_ascii=False)
            break
        else:
            msg_stack.append(content.split('$$$')[0])
            messages.append(
                {
                    "role": "system",
                    "content": content
                }
            )
            reply += f'reasoning:\n{reasoning_content}\ncontext:\n{content.split('$$$')[0]}\n'
            msg.append(tic)
            tic += 1
            sys_cmd = content.split('$$$')[1]
            with open(f'./logs/{TIME_STAMP}.json','w',encoding='utf-8') as f:
                json.dump(messages,f,indent=4,ensure_ascii=False)
            try:
                if cmd_check == sys_cmd:
                    if stage_break:
                        reply += f'[c] command refused, stage terminated\n'
                        msg_stack.append(f'[D] command refused, stage terminated')
                        break
                    else:
                        reply += f'[c] command refused\n'
                        msg_stack.append(f'[D] command refused')
                        cmd = 'Agent已驳回重复指令，进行下一项任务。'
                else:
                    cmd_check = copy.deepcopy(sys_cmd)
                    sys_cmd = sys_cmd.split(' ',maxsplit=2)
                    if sys_cmd[0] == 'dir':
                        path = sys_cmd[1]
                        cmd = tools.dir(path)
                        reply += f'[c] command [dir] excuted\n'
                        msg_stack.append(f'[D] command [dir] excuted')
                    elif sys_cmd[0] == 'listdir':
                        path = sys_cmd[1]
                        cmd = tools.list_dir(path)
                        reply += f'[c] command [listdir] excuted\n'
                        msg_stack.append(f'[D] command [listdir] excuted')
                    elif sys_cmd[0] == 'read':
                        path = sys_cmd[1]
                        cmd = tools.read(path)
                        reply += f'[c] command [read] [{path}] excuted\n'
                        msg_stack.append(f'[D] command [read] [{path}] excuted')
                    elif sys_cmd[0] == 'write':
                        path = sys_cmd[1]
                        content = sys_cmd[2]
                        cmd = tools.write(path,content)
                        reply += f'[c] command [write] [{path}] excuted\n'
                        msg_stack.append(f'[D] command [write] [{path}] excuted')
                    elif sys_cmd[0] == 'delete':
                        path = sys_cmd[1]
                        cmd = tools.delete(path)
                        reply += f'[c] command [delete] [{path}] excuted\n'
                        msg_stack.append(f'[D] command [delete] [{path}] excuted')
                    elif sys_cmd[0] == 'imread':
                        path = sys_cmd[1]
                        cmd = tools.encode_image(path)
                        reply += f'[c] command [imread] [{path}] excuted\n'
                        msg_stack.append(f'[D] command [imread] [{path}] excuted')
                    else:
                        cmd = 'command not found'
            except Exception as e:
                cmd = str(e)
    return reply

#直接使用方式
while True:
    cmd = input()
    CNMD(cmd)
    #print(msg)
    #for i in nodelist:
    #    print(i.id,i.message)