from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from schema.schemas import BasicPrompt,ProPrompt
from services.chat_service import get_friendly_responses, get_detailed_responses
from services.file_service import process_file_and_query
import httpx
import boto3
import uuid as uuid
from config import BUCKET_NAME, REGION_NAME, ACCESS_KEY, AWS_SECRET_KEY

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"]
)

s3_client = boto3.client(
    's3',
    region_name=REGION_NAME,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def upload_file_to_s3(file_content:bytes, file_name:str) -> str:
    unique_file_name = f"{uuid.uuid4()}_{file_name}"
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=unique_file_name,
            Body=file_content
        )

        return unique_file_name
    except Exception as e:
        print(f"Error uploading file to S3: {e}")
        return None

def generate_presigned_url(s3_key:str, expiry:int) -> str:
    try:
        url=s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket':BUCKET_NAME,
                'Key':s3_key
            },
            ExpiresIn=expiry
        )
        
        return url
    except Exception as e:
        print(f"Error generating presigned URL: {e}")
        return None


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

    s3_key = upload_file_to_s3(content,file.filename)
    presigned_url = generate_presigned_url(s3_key, expiry=600)
    ai_response = process_file_and_query(presigned_url, message, file.filename)
    
    return {"user":{"message":message, "file":file.filename},"ai":ai_response}