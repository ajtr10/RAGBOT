## RAGBOT – PDF Q&A Chatbot (FastAPI + Streamlit + Pinecone + Groq)

### Overview
RAGBOT is a Retrieval-Augmented Generation (RAG) chatbot that answers questions from your uploaded PDFs. It:
- Ingests PDFs → splits into chunks → embeds via HuggingFace
- Stores embeddings in Pinecone (serverless)
- Retrieves the most relevant chunks per question
- Prompts a Groq LLM with a grounded prompt to produce concise answers with citations

### Key Features
- Multiple PDF upload and indexing
- Deterministic answers (temperature=0) grounded in retrieved context
- Optional filtering by a specific PDF (`source` metadata)
- Debug logs show number of retrieved docs, sources, and small context snippets
- Simple Streamlit client for upload and chat

### Architecture
- Client (Streamlit)
  - `client/app.py`: page assembly
  - `client/components/upload.py`: PDF uploader → calls `/upload_pdfs/`
  - `client/components/chatUI.py`: chat → calls `/ask/`
  - `client/utils/api.py`: small HTTP helpers
- Server (FastAPI)
  - `server/working_main.py`: all endpoints and RAG pipeline
    - `/upload_pdfs/`: parse → split → embed → upsert to Pinecone
    - `/ask/`: retrieve from Pinecone → `RetrievalQA` with Groq → answer + sources
    - `/sources`: list ingested PDFs (names under `uploaded_pdfs/`)
  - `server/logger.py`: logging

### Tech Stack
- FastAPI, Streamlit
- LangChain (`RetrievalQA`, `PromptTemplate`)
- Pinecone (vector DB), HuggingFace embeddings (`sentence-transformers/all-MiniLM-L12-v2`, 384-dim)
- Groq LLM (`llama-3.3-70b-versatile`)

### Requirements
Install Python 3.11+ and create a virtual environment.

```bash
python -m venv venv_pinecone
venv_pinecone\Scripts\activate  # Windows PowerShell: .\venv_pinecone\Scripts\Activate.ps1
pip install -r server/requirements.txt
```

### Environment Variables
Create a `.env` file in repo root or set system env vars:

```env
PINECONE_API_KEY=your_pinecone_key
GROQ_API_KEY=your_groq_key
# Optional – keep consistent across upload and ask if you use it
PINECONE_NAMESPACE=resumes
```

### Run the Server
```bash
uvicorn server.working_main:app --reload
```
Server starts at `http://localhost:8000`.

### Run the Client (Streamlit)
```bash
streamlit run client/app.py
```

### API Endpoints
- POST `/upload_pdfs/`
  - Form field: `files` (one or more PDFs)
  - Response: `{ message, chunks_processed, index_name }`
- POST `/ask/`
  - JSON: `{ "question": "...", "source": "uploaded_pdfs/your.pdf"? }`
  - Response: `{ response, sources[] }`
- GET `/sources`
  - Response: `{ sources: ["uploaded_pdfs/a.pdf", ...] }`
- GET `/test`
  - Health check

### Typical Workflow
1) Start server
2) Upload PDFs via Streamlit sidebar (Upload to DB)
3) Ask questions in chat (optionally target a specific PDF by `source`)

### How It Works (Server)
- Upload
  - Loads PDFs with `PyPDFLoader`, splits via `RecursiveCharacterTextSplitter`
  - Embeds with `HuggingFaceEmbeddings(all-MiniLM-L12-v2)`
  - Upserts to Pinecone index `rag-minillm-384` using `langchain_pinecone.PineconeVectorStore`
- Ask
  - Builds retriever from Pinecone with `k=10`, `score_threshold=0.2`
  - Optional metadata filter: `{ source: { $eq: "uploaded_pdfs/your.pdf" } }`
  - Uses grounded prompt: answer only from context; if missing, say “I don’t know.”
  - LLM: `ChatGroq` with `temperature=0.0`

### Troubleshooting
- “I don’t know” often means no relevant chunks were retrieved:
  - Ensure you uploaded first and got “Added N chunks…”
  - Keep `PINECONE_NAMESPACE` consistent for upload and ask
  - Try increasing `k` (e.g., 10 → 12) or lowering `score_threshold` (e.g., 0.2 → 0.15)
  - Ask more specific questions or target a PDF via `source`
- Pinecone SDK errors
  - This repo uses the new SDK (`from pinecone import Pinecone`) and `langchain_pinecone`
  - If you used older imports, update to `langchain_pinecone` and new client

### Notes
- Citations are returned as file paths stored in metadata (`source`)
- Debug logs show retrieval counts, sources, and short context snippets
- Index is serverless by default in `us-east-1` (adjust in code if needed)

### License
MIT


