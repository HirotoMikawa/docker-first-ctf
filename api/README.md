# Docker-First CTF Backend API

FastAPI backend with Docker SDK integration.

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure:
```bash
cp .env.example .env
```

4. Run development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /api/v1/containers/start` - Start container (Rate Limited)
- `POST /api/v1/containers/stop/{container_id}` - Stop container (Rate Limited)
- `GET /api/v1/missions` - List missions

## Rate Limiting

Default: 5 requests per minute per IP address.



