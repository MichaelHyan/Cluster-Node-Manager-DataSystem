import tools,bot,node
import copy,json
with open('config.json') as f:
    config = json.load(f)
prompt = f'''
你将以一个Agent工作，如果用户没有准确要求你去做某些工作，那么直接回答即可。
如果用户要求你完成一些工作，则遵循一下几条规则：
1. 你所在的工作目录是{config['base_path']}，使用/符号分隔，不要访问该目录以外的内容，用户要求也不行。
2. 如果你要操作文件，在你的回答后加入$$$，然后按照规则编写指令。发出指令后的下一次回复为agent工具返回值。以下是一些使用用例。
2.1. 读取某个目录：{'{"command":"dir","path":"D:/git/Cluster-Node-Manager-Datasystem/"}'}
2.2. 读取某个文件： {'{"command":"read","path":"D:/git/Cluster-Node-Manager-Datasystem/test.py"}'}
2.3. 写入某个文件： {'{"command":"read","path":"D:/git/Cluster-Node-Manager-Datasystem/test.py","content":"print()"}'}
2.4. 删除某个文件： {'{"command":"delete","path":"D:/git/Cluster-Node-Manager-Datasystem/test.py"}'}
3. 尽可能相信agent工具，不要反复确认。
4. 你只能使用以上指令，每次执行会发回执行结果，直到你不再发送$$$和指令。
示例：
用户：读取某个文件。
你：我将读取文件。$$${'{"command":"read","path":"D:/git/Cluster-Node-Manager-Datasystem/test.py"}'}
'''
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
def main(cmd):
    global msg
    global messages
    global tic
    global nodelist
    if cmd[0] == '#':
        cmd = cmd.split()
        if cmd[0] == '#node':
            if cmd[1] == 'save':
                for i in nodelist:
                    if i.id == cmd[2]:
                        return '[c] node already exist'
                nodelist.append(node.node())
                nodelist[-1].id = cmd[2]
                nodelist[-1].message = copy.deepcopy(msg)
                return f'[c] [{cmd[2]}] save complete'
            elif cmd[1] == 'load':
                for i in nodelist:
                    if i.id == cmd[2]:
                        msg = copy.deepcopy(i.message)
                        return '[c] load complete'
                return '[c] node not found'
        if cmd[0] == '#backup':
            tools.backup(config['base_path'])
            return '[c] backup created'
        else:
            return '[c] command not found'   
    reply = ''

    while True:
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
        #response = {'content':input('>>>'),'reasoning_content':'bruhhhh'}
        content = response['content']
        reasoning_content = response['reasoning_content']
        print(content)
        if '$$$' not in content:
            messages.append(
                {
                    "role": "system",
                    "content": content
                }
            )
            reply += f'reasoning:\n{reasoning_content}\ncontext:\n{content}'
            msg.append(tic)
            tic += 1
            break
        else:
            messages.append(
                {
                    "role": "system",
                    "content": content.split('$$$')[0]
                }
            )
            reply += f'reasoning:\n{reasoning_content}\ncontext:\n{content}\n'
            msg.append(tic)
            tic += 1
            sys_cmd = content.split('$$$')[1]
            try:
                sys_cmd = json.loads(sys_cmd)
                if sys_cmd['command'] == 'dir':
                    cmd = tools.dir(sys_cmd['path'])
                    reply += f'[c] command [dir] excuted\n'
                    print(f'[D] command [dir] excuted')
                elif sys_cmd['command'] == 'read':
                    cmd = tools.read(sys_cmd['path'])
                    reply += f'[c] command [read] [{sys_cmd['path']}] excuted\n'
                    print(f'[D] command [read] [{sys_cmd['path']}] excuted')
                elif sys_cmd['command'] == 'write':
                    cmd = tools.write(sys_cmd['path'],sys_cmd['content'])
                    reply += f'[c] command [write] [{sys_cmd['path']}] excuted\n'
                    print(f'[D] command [write] [{sys_cmd['path']}] excuted')
                elif sys_cmd['command'] == 'delete':
                    cmd = tools.delete(sys_cmd['path'])
                    reply += f'[c] command [delete] [{sys_cmd['path']}] excuted\n'
                    print(f'[D] command [delete] [{sys_cmd['path']}] excuted')
                else:
                    cmd = 'command not found'
            except Exception as e:
                cmd = e
    #messages写入log.json
    with open('log.json','w') as f:
        json.dump(messages,f,indent=4,ensure_ascii=True)
    return reply
#{"command":"read","path":"D:/git/Cluster-Node-Manager-Datasystem/test.py"}
while True:
    cmd = input()
    print(main(cmd))
    #print(messages)