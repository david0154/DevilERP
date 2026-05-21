"""
Devil ERP — AI Bill Scanner
Pipeline: Upload (JPG/PNG/PDF) → OCR → Gemma AI → JSON → ERP Entry
Supports: vendor invoices, purchase bills, GST invoices
"""

from pathlib import Path
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import cv2
import numpy as np

class BillScanner:
    """
    AI OCR Pipeline:
    1. Load image/PDF
    2. Pre-process (denoise, threshold)
    3. Tesseract OCR extraction
    4. Gemma AI structuring → JSON
    5. Push to ERP (invoice + ledger + inventory)
    """

    def __init__(self):
        from ai.ai_engine import get_ai
        self.ai = get_ai()

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Enhance image for better OCR accuracy."""
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        _, thresh = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresh

    def extract_text_from_image(self, image_path: str) -> str:
        """OCR text extraction from image file."""
        processed = self.preprocess_image(image_path)
        pil_img = Image.fromarray(processed)
        text = pytesseract.image_to_string(pil_img, lang='eng+hin')
        return text.strip()

    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF bill."""
        doc = fitz.open(pdf_path)
        full_text = ""
        for page in doc:
            full_text += page.get_text()
        return full_text.strip()

    def scan(self, file_path: str) -> dict:
        """
        Main scan pipeline.
        Returns structured invoice dict ready for ERP entry.
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        # Step 1: Extract raw text
        if ext == '.pdf':
            raw_text = self.extract_text_from_pdf(str(file_path))
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            raw_text = self.extract_text_from_image(str(file_path))
        else:
            return {"error": f"Unsupported file format: {ext}"}

        if not raw_text:
            return {"error": "No text detected in the file."}

        # Step 2: AI structures the OCR text → JSON
        invoice_data = self.ai.analyze_invoice_json(raw_text)

        # Step 3: Save raw OCR + AI result to DB
        self._save_scan_log(str(file_path), raw_text, invoice_data)

        return invoice_data

    def _save_scan_log(self, file_path: str, raw_text: str, ai_json: dict):
        """Log scanned bill to database."""
        import sqlite3, json
        from core.config import BASE_DIR
        db_path = BASE_DIR / "database" / "devil_erp.sqlite"
        try:
            conn = sqlite3.connect(db_path)
            conn.execute(
                "INSERT INTO ai_scanned_bills (file_path, raw_ocr_text, ai_json, status) VALUES (?, ?, ?, ?)",
                (file_path, raw_text, json.dumps(ai_json), "processed" if ai_json else "failed")
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[BillScanner] Log error: {e}")
