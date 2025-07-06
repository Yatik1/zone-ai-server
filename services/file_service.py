import hashlib
from openai import OpenAI
from config import GEMINI_SECRET_KEY, QDRANT_URL, MODEL_NAME, API_KEY
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
import requests
from tempfile import NamedTemporaryFile

client = OpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def process_file_and_query(presigned_url:str, message:str,filename:str):

    response = requests.get(presigned_url)
    response.raise_for_status() 

    file_content = response.content

    is_pdf = filename.endswith(".pdf")

    with NamedTemporaryFile(delete=False, suffix='.pdf' if is_pdf else '.txt') as file_name:
        file_name.write(file_content)
        file_path = file_name.name


    loader = PyPDFLoader(file_path) if is_pdf else TextLoader(file_path)
    docs = loader.load() 

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 450, 
        chunk_overlap = 100, 
        separators = ["\n\n","\n"," ","."]
    )

    chunks = splitter.split_documents(documents = docs)

    embedder = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_SECRET_KEY
    )

    file_hash = hashlib.md5(file_content).hexdigest()
    qdrant_client = QdrantClient(host="localhost", port=6333)

    if not qdrant_client.collection_exists(f"{file_hash}_embeddings"):
        store = QdrantVectorStore.from_documents(
            documents=[],
            url=QDRANT_URL,
            collection_name=f"{file_hash}_embeddings",
            embedding=embedder
        )

        store.add_documents(documents=chunks)
    
    retriever = QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        collection_name=f"{file_hash}_embeddings",
        embedding = embedder
    )

    relevant_chunks = retriever.similarity_search(query = message)

    FILE_PROMPT = f"""
        You are an AI assistant who can skilled and experience in analysing and understanding the given chunks of text.
        You're job is to read, analyse and understands the given chunks based on the query given by the user. 

        The chunks that are given to you are already embedded from the vectors. All you have to do is to carfully analyse and understands these chunks,
        and then give a response to the user's query based on your analysis and understanding.

        See you also have to understand which file is document and pdf. Since both will have different metadata and concept. 

        Below are chunks from a file named {filename}.

        Analyze these chunks based on the user's query and respond accordingly.
        {relevant_chunks}

        So if the question is from the document, you will asnwer in particular format :- 
         - According to the document provided, {filename} the answer is whatever answer you have found

        But in the case of pdf, you will also have to write down the page number of the relevant chunk you have found relevant

        The Rules you have to follow when giving responses:
        - You should first read, analyse and understand the chunks given to you.
        - Then you will read, analyse and understand the query that user gave. You will understand that what user is actually asking.
        - Then you will give a response to the user based on you analysis and understanding of the chunks you are given and the query that user gave.
        - Also analyse what kind of file did the user gave. If file is document then generate response accordingly and if file is pdf then return different response with the page number.
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role":"system","content":FILE_PROMPT},
            {"role":"user", "content":message}
        ]
    )

    return response.choices[0].message.content
