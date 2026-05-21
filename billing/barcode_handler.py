"""
Devil ERP — Barcode Handler
Generates and reads product barcodes using python-barcode / pyzbar
"""
from pathlib import Path
import io


def generate_barcode(product_sku: str, save_path: str = None):
    """
    Generates a Code128 barcode image.
    Returns PIL Image or saves to path.
    """
    try:
        import barcode
        from barcode.writer import ImageWriter
        code = barcode.get("code128", product_sku, writer=ImageWriter())
        if save_path:
            code.save(save_path.replace(".png", ""))
            return save_path
        buffer = io.BytesIO()
        code.write(buffer)
        buffer.seek(0)
        return buffer
    except ImportError:
        return None


def decode_barcode(image_path: str):
    """
    Decodes barcode from image.
    Returns decoded string or None.
    """
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
        img = Image.open(image_path)
        decoded = decode(img)
        if decoded:
            return decoded[0].data.decode("utf-8")
    except ImportError:
        pass
    return None
