from fastapi import FastAPI
from openai import OpenAI
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from prompts.friendly_prompt import friendly_response
from prompts.professional_prompt import pro_prompt

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials=True, 
    allow_methods = ["*"],
    allow_headers=["*"]
)

client = OpenAI(
    api_key=os.getenv("API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

class BasicPrompt(BaseModel):
    message:str

class ProPrompt(BaseModel):
    query:str

@app.post("/chats")
def chat(prompt:BasicPrompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role":"system" , "content": friendly_response},
            {"role":"user", "content": prompt.message}
        ]
    )
    
    return {"user":prompt.message,"ai": response.choices[0].message.content}


@app.post("/ask")
def detailed_response(prompt:ProPrompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role":"system" , "content": pro_prompt},
            {"role":"user", "content": prompt.query}
        ]
    )
    
    return {"user":prompt.query,"ai": response.choices[0].message.content}