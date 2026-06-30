import json
from openai import OpenAI

config = {}
config_model = {}
client = OpenAI(api_key='API_KEY',
                base_url='BASE_URL')

def reload():
    global config,config_model,client
    with open('config.json',encoding='utf-8') as f:
        config = json.load(f)
    with open('config_model.json',encoding='utf-8') as f:
        config_model = json.load(f)
    client = OpenAI(
        api_key=config['API_KEY'],
        base_url=config['BASE_URL']
    )

def reply(message):
    try:
        response = client.chat.completions.create(
            model=config['MODEL'],
            messages=message,
            stream=False,
            **config_model
        )
        try:
            if response.choices and len(response.choices) > 0:
                message = response.choices[0].message
                if hasattr(message, 'content'):
                    content = message.content
                if hasattr(message, 'reasoning_content'):
                    reasoning_content = message.reasoning_content
                else:
                    reasoning_content = None 
        except Exception as e:
            return {
            'content':f'[D] response failed: {e}',
            'reasoning_content':'[D] response failed'
        }
        result = {
            'content':content,
            'reasoning_content':reasoning_content
        }
        return result
    except Exception as e:
        print(str(e))
        return None
reload()