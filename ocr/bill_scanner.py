"""
Devil ERP — AI Bill Scanner
OCR pipeline: Image/PDF → Text → Local AI → Structured JSON → ERP Entry
Uses pytesseract + local Gemma GGUF (via llama-cpp-python)
"""
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"


class BillScanner:
    def __init__(self, model_path: str = None):
        self.model_path = model_path or str(MODELS_DIR / "gemma-2b-it.gguf")
        self._llm = None

    def _load_llm(self):
        if self._llm is not None:
            return
        try:
            from llama_cpp import Llama
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=2048,
                n_threads=4,
                verbose=False
            )
        except Exception as e:
            print(f"[OCR] AI model not loaded: {e}")
            self._llm = None

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract raw text using pytesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(image_path)
            return pytesseract.image_to_string(img, lang="eng")
        except Exception as e:
            return f"[OCR Error] {e}"

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        try:
            import pdfplumber
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            return f"[PDF Error] {e}"

    def _extract_with_ai(self, raw_text: str) -> dict:
        """Send raw OCR text to local Gemma for structured extraction."""
        self._load_llm()
        prompt = f"""You are an invoice parsing assistant for Indian businesses.
Extract the following fields from this invoice text and return ONLY valid JSON:
{{
  "vendor_name": "",
  "vendor_gstin": "",
  "vendor_phone": "",
  "vendor_address": "",
  "invoice_number": "",
  "invoice_date": "",
  "payment_method": "",
  "line_items": [
    {{"description": "", "qty": 0, "unit_price": 0, "tax_rate": 0, "discount": 0, "amount": 0}}
  ],
  "subtotal": 0,
  "tax_amount": 0,
  "total": 0
}}

Invoice Text:
{raw_text[:2000]}

JSON Output:"""

        if self._llm:
            try:
                result = self._llm(prompt, max_tokens=1024, temperature=0.1)
                response = result["choices"][0]["text"]
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception as e:
                print(f"[OCR AI] Parse error: {e}")

        # Fallback: regex-based extraction
        return self._regex_extract(raw_text)

    def _regex_extract(self, text: str) -> dict:
        """Fallback regex extractor for common Indian invoice formats."""
        result = {
            "vendor_name": "", "vendor_gstin": "", "vendor_phone": "",
            "vendor_address": "", "invoice_number": "", "invoice_date": "",
            "payment_method": "cash", "line_items": [],
            "subtotal": 0.0, "tax_amount": 0.0, "total": 0.0
        }
        gstin = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', text)
        if gstin:
            result["vendor_gstin"] = gstin.group()
        phone = re.search(r'\b(?:\+91[-\s]?)?[6-9]\d{9}\b', text)
        if phone:
            result["vendor_phone"] = phone.group()
        inv_no = re.search(r'(?i)(?:invoice|bill|inv)\s*(?:no\.?|number|#)?\s*:?\s*([A-Z0-9\-/]+)', text)
        if inv_no:
            result["invoice_number"] = inv_no.group(1)
        date = re.search(r'\b(\d{1,2}[/\-.]\d{1,2}[/\-.](?:\d{4}|\d{2}))\b', text)
        if date:
            result["invoice_date"] = date.group()
        total = re.search(r'(?i)(?:total|grand total|net amount)[\s:]*(?:rs\.?|inr|\u20b9)?\s*([\d,]+\.?\d*)', text)
        if total:
            result["total"] = float(total.group(1).replace(",", ""))
        return result

    def scan(self, file_path: str) -> dict:
        """
        Main entry point. Accepts image (JPG/PNG) or PDF.
        Returns structured invoice data dict.
        """
        path = Path(file_path)
        if not path.exists():
            return {"error": "File not found"}

        suffix = path.suffix.lower()
        if suffix in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
            raw_text = self.extract_text_from_image(file_path)
        elif suffix == ".pdf":
            raw_text = self.extract_text_from_pdf(file_path)
        else:
            return {"error": f"Unsupported file type: {suffix}"}

        extracted = self._extract_with_ai(raw_text)
        extracted["raw_ocr_text"] = raw_text[:500]
        return extracted

    def create_erp_entry(self, scan_result: dict, db, billing_manager):
        """
        Auto-creates ERP purchase entry from scanned invoice.
        Returns (invoice_id, invoice_no, total)
        """
        # Ensure vendor exists
        vendor_name = scan_result.get("vendor_name") or "Unknown Vendor"
        party = db.fetchone(
            "SELECT id FROM parties WHERE name=? AND party_type='vendor'",
            (vendor_name,)
        )
        if not party:
            db.execute("""
                INSERT INTO parties (name, party_type, gstin, phone)
                VALUES (?,?,?,?)
            """, (vendor_name, "vendor",
                   scan_result.get("vendor_gstin", ""),
                   scan_result.get("vendor_phone", "")))
            party = db.fetchone(
                "SELECT id FROM parties WHERE name=? AND party_type='vendor'",
                (vendor_name,)
            )
        party_id = party[0]

        lines = scan_result.get("line_items", [])
        if not lines:
            lines = [{"description": "Auto-scanned purchase",
                      "qty": 1,
                      "unit_price": scan_result.get("total", 0),
                      "tax_rate": 0, "discount": 0}]

        return billing_manager.create_invoice(
            party_id=party_id,
            lines=lines,
            inv_type="purchase",
            payment_method=scan_result.get("payment_method", "cash"),
            notes=f"Auto-created from scanned invoice {scan_result.get('invoice_number','')}"
        )
