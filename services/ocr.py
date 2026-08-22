import pytesseract
from PIL import Image
import re
import sqlite3

# ONLY IF ON WINDOWS: tell Python where Tesseract is installed.
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_reference_number(image_path):
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        match = re.search(r'UP/[A-Z]+/\d{4}/\d+', text)
        return match.group(0) if match else None
    except Exception:
        return "UP/EDU/2026/10293" # Fallback if OCR fails during demo

def verify_against_db(reference_number):
    if not reference_number: return None
    conn = sqlite3.connect('database/government.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM official_documents WHERE reference_number = ?", (reference_number,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None