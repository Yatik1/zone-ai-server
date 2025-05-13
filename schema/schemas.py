from pydantic import BaseModel

class BasicPrompt(BaseModel):
    message:str

class ProPrompt(BaseModel):
    query:str