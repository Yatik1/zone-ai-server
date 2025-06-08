from pydantic import BaseModel

class BasicPrompt(BaseModel):
    message:str
    chat_id:str
    user_id:str

class ProPrompt(BaseModel):
    query:str