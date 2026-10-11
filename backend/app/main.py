"""ASGI entrypoint. Run with: uvicorn app.main:app --port $API_PORT"""

from .config import settings
from .factory import create_app

app = create_app(settings)
