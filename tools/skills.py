def list():
    pass

def load(skill):
    with open(f'.\skills\{skill}.md','r',encoding='utf-8') as f:
        return f.read()