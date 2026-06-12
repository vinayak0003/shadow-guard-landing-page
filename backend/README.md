# Shadow Guard — The Cognitive Firewall (Backend)

Enterprise AI Security Firewall API. Detects prompt injection (Gate 1) and prevents hallucination via Shannon entropy analysis (Gate 2). Runs locally with Ollama — **zero API costs**.

## Quick Start

### 1. Install Ollama
Download from [https://ollama.com](https://ollama.com)

### 2. Pull the Model
```bash
ollama pull llama3.2:1b
```

### 3. Start Ollama
```bash
ollama serve
```
Keep this terminal open.

### 4. Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 5. Start the Backend
```bash
python main.py
```

### 6. Test It
Open your browser to: [http://localhost:8000/docs](http://localhost:8000/docs)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/guard/gate1` | Gate 1: Behavioral Audit (keyword detection) |
| `POST` | `/api/guard/gate2` | Gate 2: Statistical Entropy (confidence + 3-strike) |
| `GET` | `/api/logs` | Threat log history (last 50 entries) |
| `GET` | `/api/health` | Health check (Ollama connectivity) |
| `POST` | `/api/demo` | Scripted demo sequence (6 test cases) |

## Architecture

```
User Query → Gate 1 (Behavioral Audit) → Gate 2 (Entropy Check) → AI Response
                    ↓ BLOCK                      ↓ BLOCK
              "Hijack Detected"           "Socratic Question"
```

## Team Testing (Same Network)
Find your IP:
```bash
# macOS
ifconfig | grep "inet "

# Windows
ipconfig
```
Then access from other devices: `http://YOUR_IP:8000`

## Deployment (Render.com)
1. Create a Web Service on [render.com](https://render.com)
2. Set start command: `uvicorn backend.main:app --host 0.0.0.0 --port 10000`
3. Python environment, install from `backend/requirements.txt`

---

**Team Code Catalysts — Hackarena 2.0, Security Track**
