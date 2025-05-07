from fastapi import FastAPI,File, UploadFile, Form
from openai import OpenAI
import os
import hashlib
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from prompts.friendly_prompt import friendly_response
from prompts.professional_prompt import pro_prompt
from langchain_community.document_loaders import TextLoader, PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient


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
    
    return {"user":{"message": prompt.message},"ai": response.choices[0].message.content}


@app.post("/ask")
def detailed_response(prompt:ProPrompt):
    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role":"system" , "content": pro_prompt},
            {"role":"user", "content": prompt.query}
        ]
    )
    
    return {"user":{"message":prompt.query},"ai": response.choices[0].message.content}


# @app.post("/upload_file")
# async def upload_file(file:UploadFile = File(...),message:str = Form(...)):
#     upload_folder_location = Path(__file__).parent / "upload" 
#     upload_folder_location.mkdir(exist_ok=True)
    
#     file_location = upload_folder_location / f"{file.filename}"

#     with open(file_location, "wb+") as file_object:
#         file_object.write(await file.read())

#     if file.filename.endswith(".pdf"):
#         loader = PyPDFLoader(file_location)
#     else:
#         loader = TextLoader(file_location)

#     doc = loader.load() 

#     text_splitter = RecursiveCharacterTextSplitter(
#         chunk_size = 450, 
#         chunk_overlap = 100, 
#         separators = ["\n\n", "\n",' '," ","."]
#     )

#     chunks =text_splitter.split_documents(documents=doc) 

#     embedder = GoogleGenerativeAIEmbeddings(
#         model = "models/embedding-001",
#         google_api_key = os.getenv("GEMINI_SECRET_KEY"),
#     )

#     vector_store = QdrantVectorStore.from_documents(
#         documents = [],
#         url="http://localhost:6333",
#         collection_name = f"{file_location.stem}_embds_collections",
#         embedding = embedder
#     )

#     vector_store.add_documents(documents = chunks)

#     retriever = QdrantVectorStore.from_existing_collection(
#         url="http://localhost:6333",
#         collection_name = f"{file_location.stem}_embds_collections",
#         embedding = embedder
#     )

#     relevant_chunks = retriever.similarity_search(
#         query = message
#     )

#     FILE_PROMPT = f"""
#         You are an AI assistant who can skilled and experience in analysing and understanding the given chunks of text.
#         You're job is to read, analyse and understands the given chunks based on the query given by the user. 

#         The chunks that are given to you are already embedded from the vectors. All you have to do is to carfully analyse and understands these chunks,
#         and then give a response to the user's query based on your analysis and understanding.

#         See you also have to understand which file is document and pdf. Since both will have different metadata and concept. 

#         The chunks are given below:
#         {relevant_chunks}

                
#         So if the question is from the document, you will asnwer in particular format :- 
#          - According to the document provided, {{document_name}} the answer is {{whatever answer you have found}}

#         But in the case of pdf, you will also have to write down the page number of the relevant chunk you have found relevant

#         The Rules you have to follow when giving responses:
#         - You should first read, analyse and understand the chunks given to you.
#         - Then you will read, analyse and understand the query that user gave. You will understand that what user is actually asking.
#         - Then you will give a response to the user based on you analysis and understanding of the chunks you are given and the query that user gave.
#         - Also analyse what kind of file did the user gave. If file is document then generate response accordingly and if file is pdf then return different response with the page number.


#     """

#     response = client.chat.completions.create(
#         model="gemini-2.0-flash",
#         messages=[
#             {"role":"system" , "content": FILE_PROMPT},
#             {"role":"user", "content": message}
#         ]
#     )
    
#     return {"user":{"message":message, "file":f"{file.filename}"},"ai": response.choices[0].message.content}


@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...), message: str = Form(...)):
    # Save uploaded file
    upload_folder_location = Path(__file__).parent / "upload"
    upload_folder_location.mkdir(exist_ok=True)
    file_location = upload_folder_location / file.filename
    file_content = await file.read()
    file_location.write_bytes(file_content)

    # Generate a hash of file content for unique collection name
    file_hash = hashlib.md5(file_content).hexdigest()
    collection_name = f"{file_hash}_embeddings"

    # Choose loader
    loader = PyPDFLoader(file_location) if file.filename.endswith(".pdf") else TextLoader(file_location)
    doc = loader.load()

    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=450, chunk_overlap=100,
        separators=["\n\n", "\n", " ", ".", "  "]
    )
    chunks = text_splitter.split_documents(documents=doc)

    # Create embedder
    embedder = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=os.getenv("GEMINI_SECRET_KEY"),
    )

    # Check if collection already exists
    qdrant_client = QdrantClient(host="localhost", port=6333)

    if not qdrant_client.collection_exists(collection_name):
        vector_store = QdrantVectorStore.from_documents(
            documents=[],
            url="http://localhost:6333",
            collection_name=collection_name,
            embedding=embedder
        )

        vector_store.add_documents(documents = chunks)
        print("chunk created")


    # Use the collection as retriever
    retriever = QdrantVectorStore.from_existing_collection(
        url="http://localhost:6333",
        collection_name=collection_name,
        embedding=embedder
    )

    # Retrieve relevant chunks
    relevant_chunks = retriever.similarity_search(query=message)
    formatted_chunks = "\n\n".join(
        [f"Page {doc.metadata.get('page', 'N/A')}: {doc.page_content}" for doc in relevant_chunks]
    )

    # File type hint
    file_type = "PDF" if file.filename.endswith(".pdf") else "document"

    # Prompt
    FILE_PROMPT = f"""
        You are an AI assistant who can skilled and experience in analysing and understanding the given chunks of text.
        You're job is to read, analyse and understands the given chunks based on the query given by the user. 

        The chunks that are given to you are already embedded from the vectors. All you have to do is to carfully analyse and understands these chunks,
        and then give a response to the user's query based on your analysis and understanding.

        See you also have to understand which file is document and pdf. Since both will have different metadata and concept. 

        
        Below are chunks from a {file_type} named {file.filename}.
        Analyze these chunks based on the user's query and respond accordingly.
        {formatted_chunks}

        So if the question is from the document, you will asnwer in particular format :- 
         - According to the document provided, {file.filename} the answer is {{whatever answer you have found}}

        But in the case of pdf, you will also have to write down the page number of the relevant chunk you have found relevant

        The Rules you have to follow when giving responses:
        - You should first read, analyse and understand the chunks given to you.
        - Then you will read, analyse and understand the query that user gave. You will understand that what user is actually asking.
        - Then you will give a response to the user based on you analysis and understanding of the chunks you are given and the query that user gave.
        - Also analyse what kind of file did the user gave. If file is document then generate response accordingly and if file is pdf then return different response with the page number.
    """

    response = client.chat.completions.create(
        model="gemini-2.0-flash",
        messages=[
            {"role": "system", "content": FILE_PROMPT},
            {"role": "user", "content": message}
        ]
    )

    return {
        "user": {"message": message, "file": file.filename},
        "ai": response.choices[0].message.content
    }