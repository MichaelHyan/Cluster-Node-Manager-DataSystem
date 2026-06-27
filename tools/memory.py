import json
import tools.bot as bot
def mem_save(dict):
    with open('./database/mem.json','r', encoding='utf-8') as f:
        data = json.load(f)
    for k,y in dict.items():
        data[k] = y
    with open('./database/mem.json','w',encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def similarity(str1, str2):
    set1 = set(str1)
    set2 = set(str2)
    intersection = set1 & set2
    union = set1 | set2
    if not union:
        return 1.0 if not intersection else 0.0
    return len(intersection) / len(union)

import json

def mem_load(keyx,rematch = False,relate = False):
    with open('./database/mem.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    dat = {}
    for k in data.keys():
        dat[k] = 0
    for i in keyx:
        for k,v in data.items():
            dat[k] += similarity(k, i)
            dat[k] += 0.5*similarity(v, i)
    sorted_items = sorted(dat.items(), key=lambda x: x[1], reverse=True)
    result = []
    for k, score in sorted_items:
        if score > 0.0001:
            result.append([k, data[k], score])
    if relate:
        with open('./database/relate.json', 'r', encoding='utf-8') as f:
            r = json.load(f)
        key = []
        keya = []
        for i in result:
            key.append(i[0])
        for k,v in r.items():
            for i in v:
                if i in key and k not in keya:
                    keya.append(k)
                    continue
        for i in keya:
            for k in r[i]:
                if k not in key:
                    result.append([k,data[k],0])
    if not result and rematch:
        matched = match(keyx)
        if matched != None:
            for i in matched:
                result.append([i,data[i]])
    return result if result else None


def analyse():
    with open('./database/mem.json','r',encoding='utf-8') as f:
        data = json.load(f)
    f = ''
    for k,y in data.items():
        f += f'{k}=>{y}\n'
    content=f'''请整理同类信息，严格按照以下格式输出总结内容。
你需要严格按照以下格式输出，不能输出额外的内容：
信息类型1=>信息1
信息类型2=>信息2

需要整理的信息类型：
对话事件类：
总结对话中提到的个信息要点，每一类为一条。
用户信息类：
用户的各类信息总结为一条。
工作流类：
每一类工作的流程和要点总结为一条。
不重要信息类：
非长期且不重要信息，不总结，抛弃。

如果你认为信息已经足够简洁，原样返回即可。

举例：输入：
用户名=>张三
姓名=>张三

输出：
用户名=>张三

以下是需要整理的字段：
{f}
'''
    c=[{
        "role":"user",
        "content": content
    }]
    reply = bot.reply(c)['content']
    c = {}
    for i in reply.split('\n'):
        if i:
            k = i.split('=>')
            c[k[0]] = k[1]
    with open('./database/mem.json','w',encoding='utf-8') as f:
        json.dump(c, f, indent=4, ensure_ascii=False)
    #relation
    f = ''
    for i in c.keys():
        f += f'{i}\n'
    content=f'''请整理同类信息，严格按照以下格式输出总结内容。
你需要严格按照以下格式输出，不能输出额外的内容：
信息1=>分类1
信息2=>分类2

你需要以以下规则整理信息：
1. 对于指代对象相同的信息指定到同一类
2. 格式为[信息关键词]=>[类型]
3. 每个信息按换行符分割
3. 只允许输出整理结果

举例：输入：
用户名 姓名 职业 昨日信息 

输出：
用户名=>用户
姓名=>用户
职业=>用户
昨日信息=>历史信息

以下是需要整理的字段：
{f}
'''
    c=[{
        "role":"user",
        "content": content
    }]
    reply = bot.reply(c)['content']
    c = {}
    for i in reply.split('\n'):
        if i:
            k = i.split('=>')
            if k[1] not in c.keys():
                c[k[1]] = []
            c[k[1]].append(k[0])
    with open('./database/relate.json','w',encoding='utf-8') as f:
        json.dump(c, f, indent=4, ensure_ascii=False)

def save(x):
    content='''请总结以上对话，并严格按照以下格式输出总结内容。
使用$$$作为分界符，每条信息用换行符分割。如:
$$$
信息类型1=>信息1
信息类型2=>信息2
...
$$$

需要整理的信息类型：
对话事件类：
总结对话中提到的个信息要点，每一类为一条。
用户信息类：
用户的各类信息总结为一条。
工作流类：
每一类工作的流程和要点总结为一条。
不重要信息类：
非长期且不重要信息，不总结，抛弃。

举例：
对话中提到用户名叫张三，是个法学教授，爱好是普法讲座，昨天写了一篇关于正当防卫的论文，后来直播涨了几十粉丝。在断案时先确定当事人意图和立场，然后根据实际行为判断当事人行为类型。
你需要总结的信息：
用户名=>张三
职业工作=>法学教授，普法，法学学术论文
昨日信息=>写了一篇关于正当防卫的论文
直播涨粉属于不重要且短时信息，所以不加
工作习惯=>先确定当事人意图和立场，然后根据实际行为判断当事人行为类型

你需要如此回答：
我将总结信息。$$$
用户名=>张三
职业工作=>法学教授，普法，法学学术论文
昨日信息=>写了一篇关于正当防卫的论文
工作习惯=>先确定当事人意图和立场，然后根据实际行为判断当事人行为类型
$$$
'''
    x.append({
        "role":"user",
        "content": content
    })
    reply = bot.reply(x)
    content = reply['content']
    content = content.split('$$$')[1].split('\n')
    c = {}
    for i in content:
        if i:
            k,v = i.split('=>')
            c[k] = v
    mem_save(c)

def match(x):
    words = ''
    with open('./database/mem.json','r', encoding='utf-8') as f:
        data = json.load(f)
    for i in data.keys():
        words +=f'{i}\n'
    content = f'''从下列关键词中提取与{x}有关的部分。
输出格式：
仅输出有关的关键词，按空格分开，不允许夹带其他内容。
如果没有相关的关键词则输出没有。
关键词列表如下：
{words}
'''
    content = [{
        "role":"user",
        "content": content
    }]
    reply = bot.reply(content)
    reply = reply['content']
    if '没有' in reply:
        return None
    else:
        return reply.split(' ')