from tools import fileedit,runcmd,webgrab,timer,memory,lang
import json,threading,time
def tool(function):
    try:
        function,args = function.split(maxsplit=1)
    except:
        args = None
    func = globals().get(function)
    if func:
        result = func(args)
    else:
        result = notfound(function)
    return result

def notfound(e):
    return {'sys':lang.lang['bot.tool.commandnotfound'],
            'cli':f'{lang.lang['cnmd.bot.toolfail']}{e}'}

def dir(path:str):
    sys = fileedit.dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.dir']}{path}'}

def listdir(path:str):
    sys = cmd = fileedit.list_dir(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.listdir']}{path}'}

def read(args:str):
    sys = fileedit.read(args)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.read']}{args}'}

def write(args:str):
    path,content = args.split(maxsplit=1)
    sys = fileedit.write(path,content)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.write']}{path}'}

def delete(path:str):
    sys = fileedit.delete(path)
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.delete']}{path}'}

def cmd(args:str):
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.cmd, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmd']}{args}'}

def cmdresult(args=None):
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

def powershell(args:str):
    runcmd.cmd_output=''
    threading.Thread(target=runcmd.pws, args=(args,)).start()
    time.sleep(5)
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.powershell']}{args}'}

def powershellresult(args=None):
    return {'sys':runcmd.cmd_output,
            'cli':f'{lang.lang['bot.agentlog.cmdresult']}'}

def timeread(args=None):
    sys = timer.timer()
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.time']}'}

def web(args:str):
    if len(args.split(maxsplit=1)) == 1:
        sys = webgrab.get_html(args)
        return {'sys':sys,
                'cli':f'{lang.lang['bot.agentlog.webgrab']}{args}'}
    else:
        exc,content = args.split(maxsplit=1)
        if exc == 'grab':
            sys = webgrab.get_html(content)
            return {'sys':sys,
                    'cli':f'{lang.lang['bot.agentlog.webgrab']}{content}'}
        elif exc == 'ping':
            sys = webgrab.ping(content)
            return {'sys':sys,
                    'cli':f'{lang.lang['bot.agentlog.ping']}{content}'}
        elif exc == 'setheader':
            json.loads(content)
            return {'sys':f'{lang.lang['bot.tool.setheader']}{content}',
                    'cli':f'{lang.lang['bot.agentlog.setheader']}{content}'}

def mem(args:str):
    mem = memory.mem_load(args.split())
    if mem != None:
        sys = f'{lang.lang['bot.tool.memory']}\n'
        for i in mem:
            sys += f'{i[0]}:{i[1]}\n'
    else:
        sys = lang.lang['bot.tool.memorynone']
    return {'sys':sys,
            'cli':lang.lang['cnmd.mem.search']}

def memr(args:str):
    mem = memory.mem_load(args.split(),relate=True)
    if mem != None:
        sys = f'{lang.lang['bot.tool.memory']}\n'
        for i in mem:
            sys += f'{i[0]}:{i[1]}\n'
    else:
        sys = lang.lang['bot.tool.memorynone']
    return {'sys':sys,
            'cli':lang.lang['cnmd.mem.search']}

def imread(path:str):
    sys = fileedit.encode(path,'#I#')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.imread']}{path}'}

def auread(path:str):
    sys = fileedit.encode(path,'#A#')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.auread']}{path}'}

def viread(path:str):
    sys = fileedit.encode(path,'#V#')
    return {'sys':sys,
            'cli':f'{lang.lang['bot.agentlog.viread']}{path}'}