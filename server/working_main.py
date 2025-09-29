from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import os
from dotenv import load_dotenv
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
    source: Optional[str] = None  # optional filter to target a specific PDF by source metadata

@app.post("/upload_pdfs/")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    try:
        logger.info(f"Received {len(files)} files")
        
        # Import required modules
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from pinecone import Pinecone, ServerlessSpec
        from langchain_pinecone import PineconeVectorStore
        import os
        from pathlib import Path
        
        # Get environment variables
        PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
        PINECONE_INDEX_NAME = "rag-minillm-384"
        PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "")
        UPLOAD_DIR = "./uploaded_pdfs"
        
        if not PINECONE_API_KEY:
            return {"message": "Please set PINECONE_API_API_KEY environment variable"}
        
        # Create upload directory
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        
        # Save uploaded files
        file_paths = []
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return {"message": f"File {file.filename} is not a PDF"}
                
            save_path = Path(UPLOAD_DIR) / file.filename
            with open(save_path, "wb") as f:
                content = await file.read()
                f.write(content)
            file_paths.append(str(save_path))
            logger.info(f"Saved file: {save_path}")
        
        # Process PDFs
        docs = []
        for path in file_paths:
            try:
                loader = PyPDFLoader(path)
                docs.extend(loader.load())
                logger.info(f"Processed PDF: {path} - {len(loader.load())} pages")
            except Exception as e:
                logger.error(f"Error processing {path}: {str(e)}")
                continue
        
        if not docs:
            return {"message": "No documents could be processed from the uploaded files"}
        
        # Split documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=100,
            length_function=len,
            separators=["\n\n", "\n", ".", " ", ""]
        )
        texts = splitter.split_documents(docs)
        logger.info(f"Split into {len(texts)} chunks")
        
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L12-v2"
        )
        
        # Initialize Pinecone
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if not
        if PINECONE_INDEX_NAME not in pc.list_indexes().names():
            logger.info(f"Creating new index: {PINECONE_INDEX_NAME}")
            pc.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,  # all-MiniLM-L12-v2 dimension
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            # Wait for index to be ready
            import time
            time.sleep(10)
        
        # Use LangChain's Pinecone integration for easier document upload
        logger.info("Adding documents to Pinecone...")
        _ = PineconeVectorStore.from_documents(
            documents=texts,
            embedding=embeddings,
            index_name=PINECONE_INDEX_NAME,
            namespace=PINECONE_NAMESPACE or None
        )
        
        logger.info(f"Successfully processed {len(texts)} document chunks and added to Pinecone")
        
        # Clean up uploaded files
        for path in file_paths:
            try:
                os.remove(path)
            except Exception as e:
                logger.warning(f"Could not delete {path}: {str(e)}")
        
        return {
            "message": f"Files processed successfully. Added {len(texts)} chunks to Pinecone index.",
            "chunks_processed": len(texts),
            "index_name": PINECONE_INDEX_NAME
        }
        
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
        from langchain.prompts import PromptTemplate
        from langchain_pinecone import PineconeVectorStore
        from pinecone import Pinecone
        import os

        # Env variables
        PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
        GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
        PINECONE_INDEX_NAME = "rag-minillm-384"
        PINECONE_NAMESPACE = os.environ.get("PINECONE_NAMESPACE", "")

        if not PINECONE_API_KEY or not GROQ_API_KEY:
            return {
                "response": "Please set PINECONE_API_KEY and GROQ_API_KEY environment variables",
                "sources": []
            }

        # Initialize Pinecone client (no explicit environment needed with serverless)
        _ = Pinecone(api_key=PINECONE_API_KEY)

        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")

        # Create LangChain Pinecone VectorStore from existing index
        vectorstore = PineconeVectorStore.from_existing_index(
            index_name=PINECONE_INDEX_NAME,
            embedding=embeddings,
            namespace=PINECONE_NAMESPACE or None
        )

        search_kwargs = {"k": 10, "score_threshold": 0.2}
        if request.source:
            # Filter retrieval to a specific source (exact match on metadata['source'])
            search_kwargs["filter"] = {"source": {"$eq": request.source}}

        retriever = vectorstore.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs=search_kwargs
        )

        # Initialize LLM
        llm = ChatGroq(
            groq_api_key=GROQ_API_KEY,
            model_name="llama-3.3-70b-versatile",
            temperature=0.0
        )

        # Grounded prompt to avoid hallucinations
        qa_prompt = PromptTemplate(
            input_variables=["context", "question"],
            template=(
                "You are a helpful assistant. Answer the question using ONLY the context.\n"
                "If the answer is not in the context, say 'I don't know.'\n\n"
                "Context:\n{context}\n\nQuestion: {question}\nAnswer:"
            ),
        )

        # Create QA chain
        chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": qa_prompt},
            return_source_documents=True
        )

        # Get response
        result = chain.invoke({"query": question})

        # Debug: log retrieval details
        try:
            retrieved = result.get("source_documents", [])
            logger.info(f"Retriever returned {len(retrieved)} documents")
            if retrieved:
                # logger.info("Sources: " + ", ".join([str(d.metadata.get("source", "")) for d in retrieved[:3]]))
                unique_sources = list(set([d.metadata.get("source", "") for d in retrieved]))
                logger.info(f"Unique sources: {unique_sources}")
                # Log small snippets to confirm context content
                snippets = []
                for d in retrieved[:2]:
                    content = d.page_content if hasattr(d, "page_content") else str(d)
                    snippets.append((content[:200] + "...").replace("\n", " "))
                logger.info("Context snippets: " + " | ".join(snippets))
        except Exception:
            pass

        # response = {
        #     "response": result["result"],
        #     "sources": [doc.metadata.get("source", "") for doc in result["source_documents"]]
        # }
        unique_sources = list(set([doc.metadata.get("source", "") for doc in result["source_documents"]]))
        response = {
             "response": result["result"],
             "sources": unique_sources,
             "document_count": len(result["source_documents"])  # Optional: include count for debugging
                   } 

        logger.info("Query processed successfully")
        return response

    except Exception as e:
        logger.exception("Error processing question")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/test")
async def test():
    return {"message": "Testing successful - Server is running!"}


@app.get("/sources")
async def list_sources():
    try:
        # Return the list of uploaded PDF file paths present in the upload directory
        upload_dir = "./uploaded_pdfs"
        if not os.path.isdir(upload_dir):
            return {"sources": []}
        sources = []
        for name in os.listdir(upload_dir):
            if name.lower().endswith(".pdf"):
                sources.append(os.path.join("uploaded_pdfs", name))
        return {"sources": sources}
    except Exception as e:
        logger.exception("Error listing sources")
        return JSONResponse(status_code=500, content={"error": str(e)})
