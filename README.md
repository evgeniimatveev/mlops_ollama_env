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

⚙️ Environment
Copy .env.example → .env and adjust as needed.

env
Copy code
# If Ollama runs on the host (Windows/macOS):
OLLAMA_URL=http://host.docker.internal:11434

# Linux: either add extra_hosts in compose or use the docker bridge IP (e.g.):
# OLLAMA_URL=http://172.17.0.1:11434

DEFAULT_MODEL=phi3:mini
ALLOWED_MODELS=phi3:mini,qwen2.5-coder:7b,llama3.1:latest,deepseek-r1:7b

# Optional tuning:
READ_TIMEOUT=300
OLLAMA_KEEP_ALIVE=30m
🚀 Quick Start
A) Using your host’s Ollama
Start Ollama & pull at least one model:

bash
Copy code
ollama serve
ollama pull phi3:mini
Create .env (see above).

Run:

bash
Copy code
docker compose up -d --build
Open:

Playground → http://127.0.0.1:8000/playground

Docs → http://127.0.0.1:8000/docs

Health → http://127.0.0.1:8000/health

B) Self-contained (Compose runs Ollama too)
Replace your compose with the variant below (see Compose with Ollama service) and:

bash
Copy code
docker compose up -d --build
🔌 Endpoints (cheat sheet)
GET /models

GET /chat?prompt=hi&model=phi3:mini

POST /chat with JSON:

json
Copy code
{"prompt":"hello","model":"phi3:mini","temperature":0.7,"top_p":0.9,"max_tokens":256}
GET /stream?prompt=...&model=...

GET /playground

GET /health

GET /warmup?model=phi3:mini (optional)

🐳 Docker
Standard compose (uses host Ollama)
yaml
Copy code
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
Compose with Ollama service (self-contained)
yaml
Copy code
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
Use Stream in the UI for perceived speed.

Warm up a model after start: GET /warmup?model=phi3:mini.

Lighter models (phi3:mini, qwen2.5-coder:7b) respond faster than deepseek-r1:7b.

🧰 Troubleshooting
502 from /health: confirm OLLAMA_URL is reachable (try curl http://<host>:11434/api/tags).

Linux host: add in compose:

yaml
Copy code
extra_hosts:
  - "host.docker.internal:host-gateway"
and keep OLLAMA_URL=http://host.docker.internal:11434.

No models listed: pull them first with ollama pull <model>.

🔁 CI/CD (optional: GitHub Container Registry)
Create .github/workflows/docker.yml:

yaml
Copy code
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
Image will be published as ghcr.io/<owner>/<repo>:main and :sha-....

📝 License
MIT — see LICENSE.

👤 Author
Evgenii Matveev
GitHub: https://github.com/evgeniimatveev
LinkedIn: https://www.linkedin.com/in/evgenii-matveev-510926276/
Portfolio: https://www.datascienceportfol.io/evgeniimatveevusa

yaml
Copy code

---

## `.env.example`

```env
# Host Ollama (Windows/macOS)
OLLAMA_URL=http://host.docker.internal:11434

# Linux alternative:
# OLLAMA_URL=http://172.17.0.1:11434

DEFAULT_MODEL=phi3:mini
ALLOWED_MODELS=phi3:mini,qwen2.5-coder:7b,llama3.1:latest,deepseek-r1:7b

# Optional
READ_TIMEOUT=300
OLLAMA_KEEP_ALIVE=30m
.dockerignore
gitignore
Copy code
__pycache__/
*.pyc
*.log
.venv/
.env
.git
.gitignore
tests/
(Optional) LICENSE (MIT)
text
Copy code
MIT License

Copyright (c) 2025 Evgenii Matveev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
[standard MIT text continues]
Quick push checklist
 README.md added

 .env.example present (and real .env not committed)

 .dockerignore present

 (optional) LICENSE

 (optional) .github/workflows/docker.yml

If you want, I can also draft a tiny CHANGELOG.md or add a screenshot block to the README.
