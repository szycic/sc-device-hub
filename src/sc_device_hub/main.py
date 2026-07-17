"""
Entry point for starting the FastAPI application server using uvicorn.
"""
from dotenv import load_dotenv
from pathlib import Path
import sys
import os
import uvicorn

load_dotenv()

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
  sys.path.insert(0, str(PACKAGE_ROOT))

from sc_device_hub.web import app

if __name__ == "__main__":
  uvicorn.run(
    app,
    host=os.getenv("HOST", "0.0.0.0"),
    port=int(os.getenv("PORT", "8000")),
    reload=False,
  )