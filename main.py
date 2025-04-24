from fastapi import FastAPI
from openai import OpenAI
import os
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

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

class Prompt(BaseModel):
    message:str

@app.post("/chats")
def chat(prompt:Prompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[{"role":"user", "content": prompt.message}]
    )

    return {"user":prompt.message,"ai": response.choices[0].message.content}