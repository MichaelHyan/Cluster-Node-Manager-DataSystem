import json
with open('config.json',encoding='utf-8') as f:
    config = json.load(f)
with open(f'./lang/{config['lang']}.json',encoding='utf-8') as f:
    lang = json.load(f)
