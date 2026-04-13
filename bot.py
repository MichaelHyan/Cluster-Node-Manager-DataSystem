import os,json
from openai import OpenAI
def reply(message):
    try:
        with open('config.json') as f:
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
            result = {
                'content':response.choices[0].message.content,
                'reasoning_content':response.choices[0].message.reasoning_content
                }
        except:
            result = {
                'content':response.choices[0].message.content
                }
        return result
    except Exception as e:
        return str(e)
