from openai import OpenAI
from config import API_KEY, MODEL_NAME
from prompts.friendly_prompt import friendly_response
from prompts.professional_prompt import pro_prompt

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def get_friendly_responses(message:str):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": friendly_response},
            {"role":"user", "content":message}
        ]
    )
    return response.choices[0].message.content


def get_detailed_responses(query:str):
    return client.chat.completions.create(
        model=MODEL_NAME,
        messages = [
            {"role":"system","content":pro_prompt},
            {"role":"user","content":query}
        ]
    ).choices[0].message.content



