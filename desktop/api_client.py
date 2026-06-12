"""
API клиент для связи с backend
"""
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict

import requests


def normalize_url(url: str) -> str:
    """Добавить протокол, если отсутствует (как на сайте)."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def get_image_mime_type(image_path: str) -> str:
    mime, _ = mimetypes.guess_type(image_path)
    allowed = {
        "image/jpeg": "image/jpeg",
        "image/png": "image/png",
        "image/gif": "image/gif",
        "image/webp": "image/webp",
    }
    return allowed.get(mime or "", "image/jpeg")


class APIClient:
    """Клиент для работы с API backend"""

    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("DESKTOP_API_URL", "http://localhost:8000")
        self.timeout = 180

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        kwargs.setdefault("timeout", self.timeout)

        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Не удалось подключиться к серверу. Запустите backend: python run.py",
            }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Превышено время ожидания ответа от сервера."}
        except requests.exceptions.HTTPError as e:
            detail = ""
            try:
                detail = response.json().get("detail", "")
            except Exception:
                pass
            return {"success": False, "error": detail or f"HTTP ошибка: {e}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def check_health(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def analyze_text(self, text: str) -> Dict[str, Any]:
        return self._request("POST", "/analyze_text", json={"text": text})

    def analyze_image(self, image_path: str) -> Dict[str, Any]:
        path = Path(image_path)
        if not path.exists():
            return {"success": False, "error": "Файл не найден"}

        mime = get_image_mime_type(image_path)
        try:
            with open(image_path, "rb") as f:
                files = {"file": (path.name, f, mime)}
                return self._request("POST", "/analyze_image", files=files)
        except Exception as e:
            return {"success": False, "error": str(e)}

    def parse_demo(self, url: str) -> Dict[str, Any]:
        return self._request("POST", "/parse_demo", json={"url": normalize_url(url)})

    def get_history(self) -> Dict[str, Any]:
        return self._request("GET", "/history")

    def clear_history(self) -> Dict[str, Any]:
        return self._request("DELETE", "/history")


api_client = APIClient()
