from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from schema.schemas import BasicPrompt,ProPrompt
from services.chat_service import get_friendly_responses, get_detailed_responses
from services.file_service import save_uploaded_file, process_file_and_query
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

@app.post("/chats")
async def chat(prompt:BasicPrompt):
    ai_response = get_friendly_responses(prompt.message)

    chat_id = prompt.chat_id

    message_payload = {
        "user_id":prompt.user_id,
        "user_query": prompt.message,
        "ai_response" : ai_response,
        "chat" : chat_id
    }


    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://localhost:8001/api/messages/{chat_id}",
                json = message_payload
            )
            print(f"Message had been stored in the database {response.status_code}")
        except httpx.RequestError as e:
            print(f"Error posting message to the database : {e}")


    return {"user":{"message":prompt.message},"ai":ai_response}

@app.post("/ask")
async def detailed_response(prompt:ProPrompt):
    ai_response = get_detailed_responses(prompt.query)

    chat_id = prompt.chat_id

    message_payload = {
        "user_id":prompt.user_id,
        "user_query": prompt.query,
        "ai_response" : ai_response,
        "chat" : chat_id
    }


    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"http://localhost:8001/api/messages/{chat_id}",
                json = message_payload
            )
            print(f"Message had been stored in the database {response.status_code}")
        except httpx.RequestError as e:
            print(f"Error posting message to the database : {e}")

    return {"user":{"message": prompt.query},"ai":ai_response}

@app.post("/upload_file")
async def upload_file(file:UploadFile = File(...), message:str = Form(...)):
    content = await file.read()
    file_hash, saved_path = save_uploaded_file(content, file.filename)
    ai_response = process_file_and_query(saved_path, file_hash, message,file.filename)
    
    return {"user":{"message":message, "file":file.filename},"ai":ai_response}