"""
Devil ERP — AI Model Installer
Detects available RAM and downloads the appropriate CPU-friendly GGUF model.

Model Selection:
  RAM < 4GB  → Phi-3 Mini (1.8B, ~1.2GB)
  RAM 4-8GB  → Gemma 2B  (~1.5GB)
  RAM > 8GB  → Gemma 2B Instruct (~2.0GB)
"""

import psutil
import requests
from pathlib import Path
from core.config import BASE_DIR, MODELS_DIR

MODEL_URLS = {
    "phi3_mini": {
        "name": "Phi-3 Mini (CPU, 1.8B)",
        "filename": "phi-3-mini-cpu.gguf",
        "url": "https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf",
        "min_ram_gb": 0,
    },
    "gemma_2b": {
        "name": "Gemma 2B (CPU-friendly)",
        "filename": "gemma-2b-cpu.gguf",
        "url": "https://huggingface.co/google/gemma-2b-GGUF/resolve/main/gemma-2b.Q4_K_M.gguf",
        "min_ram_gb": 4,
    },
}

class ModelInstaller:
    def __init__(self):
        MODELS_DIR.mkdir(exist_ok=True)

    def get_available_ram_gb(self) -> float:
        mem = psutil.virtual_memory()
        return mem.total / (1024 ** 3)

    def select_model(self) -> dict:
        ram = self.get_available_ram_gb()
        if ram >= 4:
            return MODEL_URLS["gemma_2b"]
        return MODEL_URLS["phi3_mini"]

    def download_model(self, model: dict, progress_callback=None) -> bool:
        dest = MODELS_DIR / model["filename"]
        if dest.exists():
            print(f"[ModelInstaller] Model already exists: {dest}")
            return True
        print(f"[ModelInstaller] Downloading {model['name']}...")
        try:
            resp = requests.get(model["url"], stream=True, timeout=60)
            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            with open(dest, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total:
                        progress_callback(int(downloaded / total * 100))
            print(f"[ModelInstaller] Downloaded to {dest}")
            return True
        except Exception as e:
            print(f"[ModelInstaller] Download failed: {e}")
            if dest.exists():
                dest.unlink()
            return False

    def run(self):
        """Detect RAM, select model, download, mark initialized.