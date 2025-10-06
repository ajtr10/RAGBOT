from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import logger

load_dotenv()

app = FastAPI(title="RagBot2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.middleware("http")
async def catch_exception_middleware(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception as exc:
        logger.exception("UNHANDLED EXCEPTION")
        return JSONResponse(status_code=500, content={"error": str(exc)})

class QuestionRequest(BaseModel):
    question: str

@app.post("/upload_pdfs/")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    try:
        logger.info(f"Received {len(files)} files")
        
        # Import required modules
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from pinecone import Pinecone
        import os
        from pathlib import Path
        
        # Get environment variables
        PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
        PINECONE_INDEX_NAME = "rag-minillm-384"
        UPLOAD_DIR = "./uploaded_pdfs"
        
        if not PINECONE_API_KEY:
            return {"message": "Please set PINECONE_API_KEY environment variable"}
        
        # Create upload directory
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded files
        file_paths = []
        for file in files:
            save_path = Path(UPLOAD_DIR) / file.filename
            with open(save_path, "wb") as f:
                f.write(file.file.read())
            file_paths.append(str(save_path))
        
        # Process PDFs
        docs = []
        for path in file_paths:
            loader = PyPDFLoader(path)
            docs.extend(loader.load())
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = splitter.split_documents(docs)
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")
        
        # Initialize Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if not
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,  # all-MiniLM-L12-v2 dimension
                metric="cosine"
            )
        
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Add documents to Pinecone
        for i, doc in enumerate(texts):
            # Generate embedding
            embedding = embeddings.embed_query(doc.page_content)
            
            # Prepare metadata
            metadata = {
                "text": doc.page_content,
                "source": doc.metadata.get("source", f"document_{i}")
            }
            
            # Upsert to Pinecone
            index.upsert(vectors=[{
                "id": f"doc_{i}",
                "values": embedding,
                "metadata": metadata
            }])
        
        logger.info(f"Successfully processed {len(texts)} document chunks and added to Pinecone")
        return {"message": f"Files processed and {len(texts)} chunks added to Pinecone index"}
        
    except Exception as e:
        logger.exception("Error during pdf upload")
        return JSONResponse(status_code=500, content={"error": str(e)})
    

@app.post("/ask/")
async def ask_question(request: QuestionRequest):
    try:
        question = request.question
        logger.info(f"User query: {question}")

        # Imports
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_groq import ChatGroq
        from langchain.chains import RetrievalQA
        from langchain_pinecone import PineconeVectorStore
        from pinecone import Pinecone
        import os

        # Env variables
        PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        PINECONE_INDEX_NAME = "rag-minillm-384"
        PINECONE_ENV = "us-east-1-aws"  # replace with your Pinecone environment

        if not PINECONE_API_KEY or not GROQ_API_KEY:
            return {
                "response": "Please set PINECONE_API_KEY and GROQ_API_KEY environment variables",
                "sources": []
            }

        # Initialize Pinecone
        # pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
        # pc = Pinecone(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
       

        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

        # Create LangChain Pinecone VectorStore
        # index = pc.Index(PINECONE_INDEX_NAME)
        # vectorstore = PineconeVectorStore(index, embeddings.embed_query, "text")
        vectorstore = PineconeVectorStore(
                    index_name=PINECONE_INDEX_NAME,
                    embedding=embeddings,
                    text_key="text",
                    pinecone_api_key=PINECONE_API_KEY
                )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile"
        )

        # Create QA chain
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            return_source_documents=True
        )

        # Get response
        result = chain({"query": question})

        response = {
                "response": result["result"],
                "sources": list(set([doc.metadata.get("source", "") for doc in result["source_documents"]]))
            }

        logger.info("Query processed successfully")
        return response

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/test")
async def test():
    return {"message": "Testing successful - Server is running!"}
