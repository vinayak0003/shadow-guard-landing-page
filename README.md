# Shadow Guard — The Cognitive Firewall

An enterprise-grade AI security firewall that intercepts prompt injection attacks and prevents LLM hallucinations using a dual-gate architecture with real-time threat monitoring.

## Architecture

```
User Prompt → [Gate 1: Behavioral Audit] → [Gate 2: Entropy Analysis] → Safe Response
                    │                              │
              Keyword + LLM                 Groq AI + Structural
              Classification                Confidence Scoring
                    │                              │
              Instant Block                 3-Strike Socratic
              (known attacks)               Protocol w/ Recovery
```

**Gate 1** — Hybrid detection pipeline combining fast keyword matching with Groq LLM-powered classification. Catches prompt injection, jailbreaks, role manipulation, system extraction, and security bypass attempts.

**Gate 2** — Statistical entropy engine that evaluates prompt confidence using structural analysis and AI response quality. Implements a 3-strike Socratic protocol: low-confidence prompts receive clarifying questions instead of hallucinated answers. Smart recovery resets strikes when a user submits a factual query.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 14, Tailwind CSS, Framer Motion, shadcn/ui |
| Backend | Python, FastAPI, SQLite |
| AI | Groq API (llama-3.3-70b-versatile) |
| Deployment | Vercel (frontend), Render (backend) |

## Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- [Groq API Key](https://console.groq.com/) (free tier available)

### Setup

```bash
# Clone and install frontend
git clone https://github.com/YOUR_USERNAME/shadow-guard.git
cd shadow-guard
pnpm install

# Setup backend
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure API key
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Run Locally

```bash
# Terminal 1 — Backend
cd backend && python main.py

# Terminal 2 — Frontend
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) and click **"Launch Enterprise Demo"** to test the firewall.

## Deployment

### Backend → Render
1. Push repo to GitHub
2. Create a new **Web Service** on [Render](https://render.com)
3. Set Build Command: `cd backend && pip install -r requirements.txt`
4. Set Start Command: `cd backend && python main.py`
5. Add environment variable: `GROQ_API_KEY`

### Frontend → Vercel
1. Import the repo on [Vercel](https://vercel.com)
2. Add environment variable: `NEXT_PUBLIC_BACKEND_URL` = your Render URL
3. Deploy

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/guard/gate1` | Behavioral audit scan |
| POST | `/api/guard/gate2` | Entropy analysis + 3-strike protocol |
| GET | `/api/logs` | Recent threat logs (50 most recent) |
| GET | `/api/health` | Server + LLM connectivity status |
| POST | `/api/demo` | Scripted demo sequence |

## License

MIT
