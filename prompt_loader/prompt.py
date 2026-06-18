import json
import json,platform

with open('config.json',encoding='utf-8') as f:
    config_base = json.load(f)
with open('./prompt_loader/config.json',encoding='utf-8') as f:
    config = json.load(f)

def load(prp):
    prompt = ''
    try:
        p = config[prp]
    except:
        p = None
    if p == None:
        prp = 'agent_base'
    if config[prp]['persona'] != 'none':
        with open(f'./prompt_loader/persona/{config[prp]['persona']}.md',encoding='utf-8') as f:
            prompt += f.read()
            prompt += '\n'
    if config[prp]['skills'] != 'none':
        with open(f'./prompt_loader/skills/{config[prp]['skills']}.md',encoding='utf-8') as f:
            prompt += f.read().replace('''{config['base_path']}''',config_base['base_path']).replace('''{platform.system()}''',platform.system())
            prompt += '\n'
    if config[prp]['extra'] != 'none':
        with open(f'./prompt_loader/extra/{config[prp]['extra']}.md',encoding='utf-8') as f:
            prompt += f.read()
    return prompt