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


## 📢 Stay Connected!  
💻 **GitHub Repository:** [Evgenii Matveev](https://github.com/evgeniimatveev)  
🌐 **Portfolio:** [Data Science Portfolio](https://www.datascienceportfol.io/evgeniimatveevusa)  
📌 **LinkedIn:** [Evgenii Matveev](https://www.linkedin.com/in/evgenii-matveev-510926276/) 
