from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from schema.schemas import BasicPrompt,ProPrompt
from services.chat_service import get_friendly_responses, get_detailed_responses
from services.file_service import process_file_and_query
import httpx
import uuid as uuid
from aws.s3service import upload_file_to_s3, generate_presigned_url
from config import BACKEND_DB

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
                f"{BACKEND_DB}/api/messages/{chat_id}",
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
                f"{BACKEND_DB}/api/messages/{chat_id}",
                json = message_payload
            )
            print(f"Message had been stored in the database {response.status_code}")
        except httpx.RequestError as e:
            print(f"Error posting message to the database : {e}")

    return {"user":{"message": prompt.query},"ai":ai_response}



@app.post("/upload_file")
async def upload_file(file:UploadFile = File(...), message:str = Form(...), userId:str = Form(...), chatId:str = Form(...)):

    content = await file.read()

    suffix = "pdf" if file.filename.endswith(".pdf") else "txt"

    s3_key = upload_file_to_s3(content,file.filename)
    presigned_url = generate_presigned_url(s3_key, expiry=600)
    ai_response = process_file_and_query(presigned_url, message, file.filename)

    message_payload = {
        "user_id":userId,
        "user_query": message,
        "ai_response" : ai_response,
        "chat" : chatId,
        "fileName":file.filename,
        "fileType": suffix
    }

    async with httpx.AsyncClient() as client:
        try:
            response= await client.post(
                f"{BACKEND_DB}/api/messages/{chatId}",
                json = message_payload
            )
            print(f"Message had been stored in the database {response.status_code}")
        except httpx.RequestError as e:
            print(f"Error posting file information to the database : {e}")
    
    return {"user":{"message":message, "file":file.filename},"ai":ai_response}