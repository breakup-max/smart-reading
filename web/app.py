import os
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from web.routers.upload import router as upload_router
from web.routers.chat import router as chat_router
from run import PDFQA

app = FastAPI(title="Smart-Reading API", version="1.0.0")

app.state.pdfqa_sessions = {}
app.state.api_key = os.environ.get("DASHSCOPE_API_KEY", "")

app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "api_key_configured": bool(app.state.api_key)}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")