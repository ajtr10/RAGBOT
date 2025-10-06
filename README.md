# 🤖 RAGBOT - PDF Q&A Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers questions from your uploaded PDFs using vector search and LLMs.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## ✨ Features

- 📄 **Multiple PDF Upload** - Ingest and index multiple documents
- 🔍 **Semantic Search** - Find relevant context using vector similarity
- 🎯 **Grounded Answers** - LLM responses constrained to document context
- 📌 **Source Citations** - Track which PDFs answered your question
- 🎨 **Clean UI** - Simple Streamlit interface for upload and chat
- ☁️ **Production Ready** - Deployed on AWS EC2 with PM2

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  Streamlit  │─────▶│   FastAPI    │─────▶│  Pinecone   │
│   (Client)  │      │   (Server)   │      │ (Vector DB) │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Groq LLM    │
                     │ (llama-3.3)  │
                     └──────────────┘
```

**Workflow:**
1. Upload PDFs → Parse & Chunk → Embed (HuggingFace) → Store (Pinecone)
2. Ask Question → Retrieve Top-K Chunks → Prompt LLM → Return Answer + Sources

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | Streamlit |
| **Backend** | FastAPI |
| **Vector DB** | Pinecone (serverless) |
| **Embeddings** | HuggingFace (`all-MiniLM-L12-v2`, 384-dim) |
| **LLM** | Groq (`llama-3.3-70b-versatile`) |
| **Framework** | LangChain (RetrievalQA) |
| **Deployment** | AWS EC2, PM2, Nginx |

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Pinecone API Key ([Get one here](https://www.pinecone.io/))
- Groq API Key ([Get one here](https://console.groq.com/))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ragbot.git
cd ragbot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r server/requirements.txt
```

### Configuration

Create a `.env` file in the root directory:

```env
PINECONE_API_KEY=your_pinecone_key_here
GROQ_API_KEY=your_groq_key_here
PINECONE_NAMESPACE=resumes
```

### Run Locally

**Terminal 1 - Start Backend:**
```bash
uvicorn server.working_main:app --reload --port 8000
```

**Terminal 2 - Start Frontend:**
```bash
streamlit run client/app.py
```

Access the app at `http://localhost:8501`

## 📁 Project Structure

```
ragbot/
├── client/
│   ├── app.py                    # Main Streamlit app
│   ├── components/
│   │   ├── upload.py            # PDF uploader
│   │   ├── chatUI.py            # Chat interface
│   │   └── history_download.py # Chat history
│   └── utils/
│       └── api.py               # API client
├── server/
│   ├── working_main.py          # FastAPI endpoints & RAG logic
│   ├── logger.py                # Logging configuration
│   └── requirements.txt         # Python dependencies
├── uploaded_pdfs/               # PDF storage directory
├── .env                         # Environment variables (not in repo)
├── .env.example                 # Template for .env
└── ecosystem.config.js          # PM2 configuration
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/upload_pdfs/` | Upload and index PDFs |
| `POST` | `/ask/` | Ask a question |
| `GET` | `/sources` | List uploaded PDFs |
| `GET` | `/test` | Health check |

### Example Request

```bash
# Upload PDFs
curl -X POST "http://localhost:8000/upload_pdfs/" \
  -F "files=@document.pdf"

# Ask a question
curl -X POST "http://localhost:8000/ask/" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the main topic?", "source": "uploaded_pdfs/document.pdf"}'
```

## ☁️ AWS Deployment

### Infrastructure

- **EC2 Instance:** Ubuntu 22.04 LTS (t3.medium recommended)
- **Process Manager:** PM2 for auto-restart and monitoring
- **Reverse Proxy:** Nginx (optional)
- **Security:** UFW firewall, SSH key authentication

### Deployment Steps

```bash
# 1. SSH into EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# 2. Clone repository
git clone https://github.com/yourusername/ragbot.git
cd ragbot

# 3. Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r server/requirements.txt

# 4. Configure .env
nano .env
# Add your API keys
chmod 600 .env

# 5. Install PM2
sudo npm install -g pm2

# 6. Start applications
pm2 start ecosystem.config.js
pm2 save
pm2 startup
```

Access at: `http://your-ec2-ip:8501`

## ⚙️ Configuration

### Retrieval Parameters

```python
# In server/working_main.py
search_kwargs = {
    "k": 10,                    # Top 10 chunks
    "score_threshold": 0.2      # Minimum similarity score
}
```

### LLM Settings

```python
llm = ChatGroq(
    model_name="llama-3.3-70b-versatile",
    temperature=0.0             # Deterministic output
)
```

### Pinecone Index

- **Name:** `rag-minillm-384`
- **Dimensions:** 384
- **Region:** us-east-1 (AWS serverless)

## 🐛 Troubleshooting

### "I don't know" Responses

- Verify PDFs uploaded successfully: Check `uploaded_pdfs/` directory
- Ensure consistent `PINECONE_NAMESPACE` between upload and query
- Lower `score_threshold` (0.2 → 0.15) for broader recall
- Check logs: `pm2 logs ragbot-server`

### Out of Memory (EC2)

- Upgrade from t3.small (2GB) to t3.medium (4GB)
- HuggingFace model requires ~120MB on first run
- Monitor: `free -h` and `htop`

### Connection Issues

```bash
# Check if apps are running
pm2 status

# Check ports
sudo netstat -tlnp | grep -E '8000|8501'

# Verify security group allows ports 8000, 8501 in AWS Console
```

## 📊 Performance

- **Embedding Model:** 384 dimensions, ~5MB model size
- **Retrieval Speed:** ~200ms for k=10 chunks
- **LLM Response:** ~2-4 seconds (Groq inference)
- **Memory Usage:** ~1.5GB baseline (server + client)

## 🔐 Security Best Practices

- ✅ Store API keys in `.env` (never commit to Git)
- ✅ Use `chmod 600 .env` for file permissions
- ✅ Enable UFW firewall on EC2
- ✅ Use SSH key authentication (disable password auth)
- ✅ Keep dependencies updated: `pip install --upgrade -r server/requirements.txt`

## 📝 Example Usage

1. **Upload PDFs:**
   - Click "Upload PDFs" in sidebar
   - Select one or more PDF files
   - Click "Upload to DB"

2. **Ask Questions:**
   - Type question in chat input: "What are the main findings?"
   - Get answer with source citations
   - Optionally filter by specific PDF

3. **View Sources:**
   - Sources listed below each answer
   - Format: `uploaded_pdfs/filename.pdf`

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -m 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/) for RAG framework
- [Pinecone](https://www.pinecone.io/) for vector database
- [Groq](https://groq.com/) for fast LLM inference
- [HuggingFace](https://huggingface.co/) for embedding models

## 📧 Contact

For questions or support, please open an issue or contact [your-email@example.com]

---

**Built with ❤️ using RAG architecture**
