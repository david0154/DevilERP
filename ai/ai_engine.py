"""
Devil ERP — Offline AI Engine
Uses a single CPU-friendly GGUF model (Gemma 2B or Phi-3 Mini)
for all AI tasks: analytics, predictions, OCR analysis, Q&A.

No internet required after model download.
"""

from pathlib import Path
from core.config import AI_MODEL_FILE

class DevilAI:
    """
    Single AI instance for all Devil ERP intelligence tasks.
    Handles: analytics Q&A, sales predictions, inventory alerts, OCR structuring.
    """

    def __init__(self):
        self._llm = None
        self._loaded = False

    def load_model(self):
        """Load GGUF model — lazy load on first AI use."""
        if self._loaded:
            return True
        if not AI_MODEL_FILE.exists():
            print(f"[DevilAI] Model not found at {AI_MODEL_FILE}")
            print("[DevilAI] Run installer to download the AI model.")
            return False
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=str(AI_MODEL_FILE),
                n_ctx=2048,
                n_threads=4,       # CPU threads
                n_gpu_layers=0,    # CPU only
                verbose=False,
            )
            self._loaded = True
            print("[DevilAI] Model loaded successfully.")
            return True
        except Exception as e:
            print(f"[DevilAI] Model load failed: {e}")
            return False

    def query(self, prompt: str, max_tokens: int = 512) -> str:
        """Run a business intelligence query."""
        if not self._loaded and not self.load_model():
            return "AI model not available. Please run the model installer."
        system = (
            "You are Devil ERP's business intelligence assistant. "
            "Answer only based on ERP data provided. Be concise and accurate. "
            "Format numbers in Indian Rupees (₹) where applicable."
        )
        full_prompt = f"<s>[INST] {system}\n\n{prompt} [/INST]"
        result = self._llm(full_prompt, max_tokens=max_tokens, stop=["</s>"])
        return result["choices"][0]["text"].strip()

    def analyze_invoice_json(self, ocr_text: str) -> dict:
        """Structure raw OCR text into invoice JSON."""
        prompt = f"""
Extract invoice data from this OCR text and return ONLY valid JSON:
{ocr_text}

Expected JSON format:
{{
  "vendor_name": "",
  "gstin": "",
  "invoice_number": "",
  "invoice_date": "",
  "items": [
    {{"name": "", "qty": 0, "rate": 0, "gst_rate": 0, "amount": 0}}
  ],
  "subtotal": 0,
  "cgst": 0,
  "sgst": 0,
  "igst": 0,
  "total": 0
}}
"""
        response = self.query(prompt, max_tokens=1024)
        import json, re
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return {}

    def predict_sales(self, historical_data: list) -> dict:
        """Predict next month's sales based on historical data."""
        data_str = str(historical_data[-6:])  # Last 6 months
        prompt = f"Given monthly sales data: {data_str}, predict next month's sales and top products. Return as JSON."
        return self.query(prompt)

    def detect_dead_stock(self, inventory_data: list) -> list:
        """Identify slow-moving / dead stock items."""
        prompt = f"Analyze inventory movement data and identify dead stock (no sales in 90+ days): {str(inventory_data)}. List item names."
        return self.query(prompt)

    def vendor_score(self, vendor_data: list) -> str:
        """Score vendors by profit margin, reliability, delivery."""
        prompt = f"Score these vendors by profitability and reliability: {str(vendor_data)}. Rank them 1-10."
        return self.query(prompt)


# Global AI instance (singleton)
_ai_instance = None

def get_ai() -> DevilAI:
    global _ai_instance
    if _ai_instance is None:
        _ai_instance = DevilAI()
    return _ai_instance
