# 🧠 FastAPI + Ollama Playground — Dockerized LLM Inference

![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/CI%2FCD-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

Minimal **FastAPI** service that connects to **Ollama** and ships with a tiny web **playground** (model selector, temperature, top-p, max tokens, streaming).  
Runs with one command via **Docker Compose**.

---

## 📦 Tech Stack
- **FastAPI + Uvicorn** — API & simple HTML playground  
- **Ollama** — local LLMs (phi3, qwen2.5-coder, llama3, deepseek-r1, …)  
- **Docker / Compose** — reproducible environment  
- **dotenv** — config via `.env`  
- **pytest** — optional tests (if you add them)  
- **GitHub Actions** — optional CI/CD for container images

---

## ✨ Features
- `GET /models` — proxies Ollama `/api/tags` (model list)  
- `GET/POST /chat` — non-stream response  
- `GET /stream` — token streaming (text/plain)  
- `GET /playground` — minimal web UI  
- `GET /health` — connectivity check  
- (Optional) `GET /warmup?model=phi3:mini` — preload/keep model warm

---

## 🗂️ Project Structure
```bash
.
├── app/
│   ├── __init__.py
│   └── main.py
├── .env                # local (do NOT commit)
├── .env.example        # template to share
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md

```

⚙️ Environment Setup

Copy .env.example → .env and adjust as needed.

# If Ollama runs on the host (Windows/macOS):
OLLAMA_URL=http://host.docker.internal:11434

# Linux: either add extra_hosts in compose or use the docker bridge IP (e.g.):
# OLLAMA_URL=http://172.17.0.1:11434

DEFAULT_MODEL=phi3:mini
ALLOWED_MODELS=phi3:mini,qwen2.5-coder:7b,llama3.1:latest,deepseek-r1:7b

# Optional tuning
READ_TIMEOUT=300
OLLAMA_KEEP_ALIVE=30m

🚀 Quick Start
A) Using Your Host’s Ollama

Start Ollama and pull at least one model:

ollama serve
ollama pull phi3:mini


Then build and run:

docker compose up -d --build


Access endpoints:

🎨 Playground → http://127.0.0.1:8000/playground

📘 Docs → http://127.0.0.1:8000/docs

💚 Health → http://127.0.0.1:8000/health

B) Self-contained (Compose Runs Ollama Too)

Use this version of docker-compose.yml:

version: "3.9"
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  ollama_api:
    build: .
    container_name: ollama_api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:


Then run:

docker compose up -d --build

🔌 Endpoints (Cheat Sheet)
Method	Endpoint	Description
GET	/models	List available models
GET / POST	/chat	Generate text
GET	/stream	Stream responses
GET	/playground	UI
GET	/health	Status check
GET	/warmup?model=phi3:mini	Warm up model

Example JSON for /chat:

{
  "prompt": "hello",
  "model": "phi3:mini",
  "temperature": 0.7,
  "top_p": 0.9,
  "max_tokens": 256
}

🐳 Docker Setup
Standard Compose (Uses Host Ollama)
version: "3.9"
services:
  ollama_api:
    build: .
    container_name: ollama_api
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped

Compose with Ollama Service (Self-contained)
version: "3.9"
services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped

  ollama_api:
    build: .
    container_name: ollama_api
    ports:
      - "8000:8000"
    environment:
      - OLLAMA_URL=http://ollama:11434
    depends_on:
      - ollama
    restart: unless-stopped

volumes:
  ollama_data:

⚡ Performance Tips

Use /stream for faster perceived output

Warm up models via GET /warmup?model=phi3:mini

Lightweight models (phi3:mini, qwen2.5-coder:7b) run faster than large ones

🧰 Troubleshooting

502 from /health — Check if OLLAMA_URL is reachable:

curl http://<host>:11434/api/tags


Linux fix — Add to docker-compose.yml:

extra_hosts:
  - "host.docker.internal:host-gateway"


Keep OLLAMA_URL=http://host.docker.internal:11434.

No models listed? → Run:

ollama pull phi3:mini

🔁 CI/CD (GitHub Container Registry)

.github/workflows/docker.yml:

name: Docker CI/CD
on:
  push:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build_and_push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/metadata-action@v5
        id: meta
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}


Resulting image:

ghcr.io/<owner>/<repo>:main
ghcr.io/<owner>/<repo>:sha-...

🧾 .dockerignore
__pycache__/
*.pyc
*.log
.venv/
.env
.git
.gitignore
tests/

🪪 LICENSE (MIT)
MIT License

Copyright (c) 2025 Evgenii Matveev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
[standard MIT text continues...]

✅ Quick Push Checklist

 README.md added

 .env.example included (real .env excluded)

 .dockerignore present

 (optional) LICENSE added

 (optional) .github/workflows/docker.yml for CI/CD

👤 Author

Evgenii Matveev
🌐 GitHub

💼 LinkedIn

📊 Portfolio


---

✅ Everything is in **one clean file**: README + `.env.example` + `.dockerignore` + MIT License + CI/CD + checklist.  
Perfect for a professional GitHub release.

Would you like me to add a **preview image** block at the top (like a screenshot of your playground UI)? It’ll make the repo look even more polished.

You said:
# 🧠 FastAPI + Ollama Playground — Dockerized LLM Inference
