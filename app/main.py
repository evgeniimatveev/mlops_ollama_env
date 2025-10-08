# app/main.py
# FastAPI + Ollama with a minimal web playground (English-only UI)
# - Reads OLLAMA_URL from .env (fallback http://127.0.0.1:11434)
# - /models proxies Ollama tags
# - /chat supports GET/POST with generation params
# - /stream streams tokens (text/plain)
# - /playground: simple HTML app with model/params controls

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv

import os
import json
import requests
from typing import Generator, Optional

load_dotenv(find_dotenv())

app = FastAPI(title="FastAPI + Ollama")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
SESSION_TIMEOUT = (5, 120)  # (connect, read) seconds

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatIn(BaseModel):
    prompt: str
    model: Optional[str] = "phi3:mini"
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    max_tokens: Optional[int] = 512  # Ollama uses "num_predict"

@app.get("/")
def root():
    return {"message": "FastAPI + Ollama is running 🚀"}

@app.get("/health")
def health():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        r.raise_for_status()
        data = r.json()
        names = [m.get("name") for m in data.get("models", []) if m.get("name")]
        return {"ok": True, "ollama_url": OLLAMA_URL, "models": names}
    except Exception as e:
        return JSONResponse(status_code=502, content={"ok": False, "error": str(e)})

@app.get("/models")
def models():
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=30)
        r.raise_for_status()
        data = r.json()
        names = [m.get("name") for m in data.get("models", []) if m.get("name")]
        return {"names": names, "raw": data}
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

@app.get("/chat")
def chat_get(
    prompt: str,
    model: str = "phi3:mini",
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 512,
):
    return _chat_full(prompt, model, temperature, top_p, max_tokens)

@app.post("/chat")
def chat_post(body: ChatIn):
    return _chat_full(
        body.prompt,
        body.model or "phi3:mini",
        body.temperature or 0.7,
        body.top_p or 0.9,
        body.max_tokens or 512,
    )

@app.get("/stream")
def stream_get(
    prompt: str,
    model: str = "phi3:mini",
    temperature: float = 0.7,
    top_p: float = 0.9,
    max_tokens: int = 512,
):
    gen = _chat_stream(prompt, model, temperature, top_p, max_tokens)
    return StreamingResponse(gen, media_type="text/plain")

def _make_payload(prompt: str, model: str, temperature: float, top_p: float, max_tokens: int):
    # Ollama options map (num_predict = max_tokens)
    options = {
        "temperature": float(temperature),
        "top_p": float(top_p),
        "num_predict": int(max_tokens),
    }
    return {"model": model, "prompt": prompt, "options": options}

def _chat_full(prompt: str, model: str, temperature: float, top_p: float, max_tokens: int):
    try:
        payload = _make_payload(prompt, model, temperature, top_p, max_tokens)
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=SESSION_TIMEOUT,
        ) as r:
            r.raise_for_status()
            chunks = []
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line.decode("utf-8"))
                    if "response" in obj:
                        chunks.append(obj["response"])
                except json.JSONDecodeError:
                    continue
        return {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "response": "".join(chunks),
        }
    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Timeout talking to Ollama")
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Ollama error: {e}")

def _chat_stream(
    prompt: str, model: str, temperature: float, top_p: float, max_tokens: int
) -> Generator[str, None, None]:
    try:
        payload = _make_payload(prompt, model, temperature, top_p, max_tokens)
        with requests.post(
            f"{OLLAMA_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=SESSION_TIMEOUT,
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line:
                    continue
                try:
                    obj = json.loads(line.decode("utf-8"))
                    if "response" in obj:
                        yield obj["response"]
                except json.JSONDecodeError:
                    continue
    except requests.Timeout:
        yield "[Timeout talking to Ollama]"
    except requests.RequestException as e:
        yield f"[Ollama error: {e}]"

# ---------- Minimal English-only Playground ----------
@app.get("/playground", response_class=HTMLResponse)
def playground():
    return """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Ollama Playground</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial; margin: 24px; max-width: 900px; }
    textarea, select, input { width: 100%; padding: 8px; border-radius: 8px; border: 1px solid #ccc; }
    pre { white-space: pre-wrap; background: #111; color: #eee; padding: 12px; border-radius: 8px; min-height: 120px; }
    button { margin-right: 8px; margin-top: 6px; }
    .row { margin: 12px 0; }
    .grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; }
  </style>
</head>
<body>
  <h2>Ollama Playground</h2>

  <div class="row grid">
    <div>
      <label>Model</label>
      <select id="model"></select>
    </div>
    <div>
      <label>Temperature</label>
      <input id="temperature" type="number" step="0.1" min="0" max="2" value="0.7" />
    </div>
    <div>
      <label>Top-p</label>
      <input id="top_p" type="number" step="0.05" min="0" max="1" value="0.9" />
    </div>
  </div>

  <div class="row">
    <label>Max tokens</label>
    <input id="max_tokens" type="number" min="1" max="4096" value="512" />
  </div>

  <div class="row">
    <label>Prompt</label>
    <textarea id="prompt" rows="8" placeholder="Write your prompt here..."></textarea>
  </div>

  <div class="row">
    <button onclick="preset('Give a short self-introduction and how to work with you.')">Self-intro</button>
    <button onclick="preset('Create a 30-day Python learning plan for a data analyst.')">Learning plan</button>
    <button onclick="preset('Write a Python function that removes duplicates while preserving order.')">Python code</button>
  </div>

  <div class="row">
    <button onclick="send()">Send</button>
    <button onclick="stream()">Stream</button>
    <span id="status"></span>
  </div>

  <pre id="out"></pre>

<script>
function preset(t){ document.getElementById('prompt').value = t; }

async function loadModels(){
  const sel = document.getElementById('model');
  sel.innerHTML = '';
  try{
    const res = await fetch('/models');
    const data = await res.json();
    const names = data.names ?? [];
    if(names.length === 0){ names.push('phi3:mini'); }
    for(const m of names){
      const opt = document.createElement('option');
      opt.value = m; opt.textContent = m;
      sel.appendChild(opt);
    }
  }catch(e){
    const opt = document.createElement('option');
    opt.value = 'phi3:mini'; opt.textContent = 'phi3:mini';
    sel.appendChild(opt);
  }
}

function uiParams(){
  return {
    model: document.getElementById('model').value,
    prompt: document.getElementById('prompt').value,
    temperature: parseFloat(document.getElementById('temperature').value || '0.7'),
    top_p: parseFloat(document.getElementById('top_p').value || '0.9'),
    max_tokens: parseInt(document.getElementById('max_tokens').value || '512'),
  };
}

async function send(){
  const status = document.getElementById('status');
  const out = document.getElementById('out');
  status.textContent = '⏳';
  out.textContent = '';
  const p = uiParams();
  const res = await fetch('/chat', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(p)
  });
  const data = await res.json();
  status.textContent = res.ok ? '✅' : '⚠️';
  out.textContent = data.response ?? JSON.stringify(data, null, 2);
  out.scrollTop = out.scrollHeight;
}

async function stream(){
  const status = document.getElementById('status');
  const out = document.getElementById('out');
  status.textContent = '⏳ stream';
  out.textContent = '';
  const p = uiParams();
  const url = '/stream?'
    + new URLSearchParams({
        prompt: p.prompt,
        model: p.model,
        temperature: String(p.temperature),
        top_p: String(p.top_p),
        max_tokens: String(p.max_tokens),
      }).toString();
  const res = await fetch(url);
  if(!res.ok){
    status.textContent = '⚠️';
    out.textContent = await res.text();
    return;
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  while(true){
    const {value, done} = await reader.read();
    if(done) break;
    out.textContent += decoder.decode(value);
    out.scrollTop = out.scrollHeight;
  }
  status.textContent = '✅';
}

loadModels();
</script>
</body>
</html>
    """