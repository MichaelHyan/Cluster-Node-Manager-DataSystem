import os,json
from openai import OpenAI
def reply(message):
    try:
        with open('config.json',encoding='utf-8') as f:
            config = json.load(f)
        client = OpenAI(
            api_key=config['API_KEY'],
            base_url=config['BASE_URL'])
        response = client.chat.completions.create(
            model=config['MODEL'],
            messages=message,
            stream=False
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
