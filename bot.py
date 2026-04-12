import os,json
from openai import OpenAI
def reply(message):
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
    result = {'content':response.choices[0].message.content,
              'reasoning_content':response.choices[0].message.reasoning_content
              }
    return result