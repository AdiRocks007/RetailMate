#  RetailMate - AI-Powered Shopping Assistant

*Your calendar. Your mood. Your AI shopper.*

RetailMate is an AI-powered, emotion-aware, calendar-integrated shopping assistant that uses local Ollama models for privacy-first AI inference. Built with FastAPI backend and Streamlit frontend for personalized shopping recommendations based on your mood, upcoming events, and preferences using advanced RAG (Retrieval-Augmented Generation) technology.

##  Features

- ** Intelligent AI Assistant**: Powered by Qwen 2.5 3B model with Ollama for local, privacy-focused inference
- ** Emotion-Aware**: Advanced sentiment analysis using VADER + TextBlob to tailor recommendations to your mood
- ** Calendar Integration**: Proactive shopping suggestions based on upcoming events and occasions
- ** Smart Retrieval**: RAG implementation with ChromaDB for contextual, knowledge-based responses
- ** Privacy-First**: 100% local processing - your data never leaves your machine
- ** Proactive Recommendations**: Concierge-like agentic behavior for anticipatory shopping assistance

##  Prerequisites

- **Windows OS** (10/11)
- **Python 3.11+** 
- **Git** (latest version)
- **8GB+ RAM** recommended
- **Internet connection** (for initial setup)

## Tech Stack

- **AI Framework**: Ollama (local inference)
- **AI Models**: Qwen 2.5 3B / Llama 3.1 
- **Backend**: FastAPI + Python
- **Frontend**: Streamlit
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Vector DB**: ChromaDB
- **Embeddings**: sentence-transformers

## Complete Setup Guide

### **1. Clone Repository**
```powershell
git clone https://github.com/AdiRocks007/RetailMate.git
cd RetailMate
```

### **2. Create Virtual Environment**
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Verify activation (you should see (venv) in prompt)
```

### **3. Install Python Dependencies**
```powershell
# Upgrade pip
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### **4. Install Ollama**
```powershell
# Option 1: Using winget (recommended)
winget install Ollama.Ollama

# Option 2: Download manually from https://ollama.com
# Then restart PowerShell terminal
```

### **5. Configure Environment Variables**
Create a `.env` file in the project root:
```powershell
@"
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:3b

DATABASE_URL=sqlite:///./data/retailmate.db

API_HOST=0.0.0.0
API_PORT=8000
FRONTEND_PORT=8501

DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=2048
CONTEXT_LENGTH=4096

DEBUG=true
LOG_LEVEL=INFO
ENVIRONMENT=development
"@ | Out-File -FilePath ".env" -Encoding utf8
```

### **6. Setup Ollama AI Models**
```powershell
# Start Ollama service (keep this terminal open)
ollama serve

# In a NEW terminal, pull the AI model
ollama pull qwen2.5:3b

# Test the model (optional)
ollama run qwen2.5:3b
# Type: "Hello!" to test, then "/bye" to exit
```

### **7. Test Complete Setup**
```powershell
# Run the test script to verify everything works
python test_setup.py
```

##  Running the Application

### **Start Backend API**
```powershell
# Make sure virtual environment is active
.\venv\Scripts\Activate.ps1

# Navigate to backend and start API server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# API will be available at: http://localhost:8000
```

### **Start Frontend Interface**
```powershell
# In a NEW terminal, activate environment
.\venv\Scripts\Activate.ps1

# Navigate to frontend and start Streamlit
cd frontend  
streamlit run app.py --server.port 8501

# Frontend will be available at: http://localhost:8501
```

##  Verification Commands

### **Test Ollama**
```powershell
# Check Ollama version
ollama --version

# List available models
ollama list

# Test model conversation
ollama run qwen2.5:3b
```

### **Test Python Environment**
```powershell
# Check Python packages
python -c "import ollama, streamlit, fastapi; print('✅ All packages working!')"

# Test sentence-transformers specifically
python -c "from sentence_transformers import SentenceTransformer; print('✅ Embeddings ready!')"
```

##  Troubleshooting

### **Ollama Command Not Found**
```powershell
# Restart PowerShell terminal as Administrator
# Or manually add to PATH:
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Ollama"
```

### **sentence-transformers Import Error**
```powershell
# Fix huggingface_hub compatibility
pip install huggingface_hub==0.25.2
pip install sentence-transformers
```

### **Port Already in Use**
```powershell
# Kill processes on ports 8000 or 8501
netstat -ano | findstr :8000
taskkill /PID <PID_NUMBER> /F
```

### **Virtual Environment Issues**
```powershell
# Recreate virtual environment
Remove-Item -Recurse -Force venv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

##  Project Structure

```
RetailMate/
├── backend/           # FastAPI backend
├── frontend/          # Streamlit frontend  
├── ollama/           # Ollama configurations
├── data/             # Database and embeddings
├── tests/            # Test files
├── requirements.txt  # Python dependencies
├── .env             # Environment variables
└── README.md        # This file
```

##  Performance Expectations

- **Response Time**: 3-10 seconds for typical queries
- **Inference Speed**: 2-8 tokens/second (CPU-optimized)
- **Memory Usage**: 4-7GB RAM total
- **Privacy**: 100% local processing, no external data transmission

##  Usage

### Basic Chat
1. Open the Streamlit interface at `http://localhost:8501`
2. Navigate to the Chat page
3. Start conversing with your AI shopping assistant
4. The system will analyze your mood and provide personalized recommendations

### Calendar Integration
1. Set up Google Calendar API credentials
2. Grant calendar access permissions
3. RetailMate will automatically analyze upcoming events
4. Receive proactive shopping suggestions for events

##  API Documentation

Once the backend is running, visit:
- API Documentation: `http://localhost:8000/docs`
- Alternative UI: `http://localhost:8000/redoc`

### Key Endpoints
- `POST /api/chat`: Send messages to the AI assistant
- `GET /api/sentiment`: Analyze message sentiment
- `POST /api/calendar/sync`: Synchronize calendar events
- `GET /api/health`: System health check

##  Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -m 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit pull request

##  Support

If you encounter issues:
1. Check the troubleshooting section above
2. Run `python test_setup.py` for diagnostic info
3. Open an issue on GitHub with error details

##  Acknowledgments

- [Ollama](https://ollama.ai/) for local AI inference
- [Qwen Team](https://github.com/QwenLM/Qwen) for the language model
- [ChromaDB](https://www.trychroma.com/) for vector database
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Streamlit](https://streamlit.io/) for the frontend interface

---

**RetailMate** - Built with ❤️ for privacy-conscious AI enthusiasts!
