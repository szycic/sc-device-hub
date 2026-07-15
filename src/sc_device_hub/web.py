from __future__ import annotations

import os
from dotenv import load_dotenv
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sc_device_hub.api import api_v1_router
from sc_device_hub.models import seed_devices, store

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


app = FastAPI(title="SC Device Hub")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

if STATIC_DIR.exists():
  app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(api_v1_router)


@app.on_event("startup")
async def startup_event() -> None:
  seed_devices()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
  return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={
      "devices": [device.to_payload() for device in store.list()]
    },
  )