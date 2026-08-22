import os
import pymupdf  # PyMuPDF for PDF extraction & metadata analysis
import requests
import base64
from flask import Flask, request, render_template, redirect, url_for
from flask_cors import CORS
import io
from PIL import Image
import re

# ==========================================================
# PASTE YOUR GROQ API KEY HERE
# ==========================================================
GROQ_API_KEY = "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"

# ==========================================================
# FLASK APPLICATION SETUP
# ==========================================================
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

latest_result = {
    "filename": "",
    "analysis": "",
    "status": "",
    "error": ""
}

# ==========================================================
# SIMPLE & STABLE PDF EXTRACTION
# ==========================================================
def extract_pdf_data(file_path):
    text = ""
    metadata_warnings = []
    pil_images = []
    pages_to_process = [] # Safe initialization prevents UnboundLocalError
    
    try:
        pdf = pymupdf.open(file_path)
        total_pages = len(pdf)
        meta = pdf.metadata or {}

        # Metadata analysis
        producer = str(meta.get("producer", "")).lower()
        creator = str(meta.get("creator", "")).lower()
        found_tools = [t for t in ["photoshop", "canva", "gimp", "illustrator", "ilovepdf", "pdf2go"] if t in producer or t in creator]

        if found_tools:
            metadata_warnings.append(f"WARNING: Document was modified using ({', '.join(found_tools)}).")

        # Stable page limits (First 3 and Last 1)
        if total_pages > 10:
            metadata_warnings.append(f"LARGE DOCUMENT DETECTED: ({total_pages} pages). Processed key pages for fast analysis.")
            pages_to_process = list(range(0, min(3, total_pages))) + list(range(max(3, total_pages - 1), total_pages))
        else:
            pages_to_process = list(range(total_pages))

        # Extract Text and Images safely
        for page_num in pages_to_process:
            page = pdf[page_num]
            page_text = page.get_text().strip()
            
            if page_text:
                text += f"\n--- Page {page_num + 1} ---\n" + page_text
            
            # Extract standard image if page is mostly visual
            if len(page_text) < 50:
                pix = page.get_pixmap(dpi=60)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                
                if img.width > 500:
                    ratio = 500 / img.width
                    img = img.resize((500, int(img.height * ratio)))
                    
                pil_images.append(img)

        pdf.close()

    except Exception as e:
        print(f"PDF extraction error: {e}")
        if not pages_to_process:
            pages_to_process = [0]

    # Convert a MAXIMUM of 3 images to base64 (Prevents 413 Error)
    base64_images = []
    for img in pil_images[:3]:
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=60)
        b64_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        base64_images.append(b64_str)

    metadata_info = "\n".join(metadata_warnings) if metadata_warnings else "No technical metadata flags detected."
    return text, metadata_info, base64_images

def extract_txt_text(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read(), "TXT files do not contain PDF metadata.", []
    except:
        return "", "Error reading file.", []

# ==========================================================
# GROQ AI FORGERY & VERIFICATION ANALYSIS
# ==========================================================
def analyze_forgery_and_content(document_text, metadata_info, base64_images):
    if not GROQ_API_KEY:
        return {"success": False, "error": "Groq API key is missing."}

    # Restrict text length safely
    document_text = document_text[:3000]

    prompt = f"""
You are REverifier, an expert forensic document analyst. 

CRITICAL INSTRUCTION: DO NOT write any introductions. DO NOT explain your thought process. 
START your response IMMEDIATELY with "AUTHENTICITY & TAMPER ASSESSMENT:".

METADATA FROM FILE: {metadata_info}
TEXT CONTENT: {document_text}

Provide EXACTLY this structure and absolutely nothing else:
AUTHENTICITY & TAMPER ASSESSMENT:
- VERDICT: [Pass (Likely Authentic) / Warning (Requires Review) / High Risk (Potential Forgery)]
- FORGERY ANALYSIS: Mention editing tools, odd dates, or mismatched math.
ABOUT THIS DOCUMENT:
DOCUMENT TYPE:
SUMMARY:
KEY POINTS & DETAILED BREAKDOWN:
IMPORTANT DATES:
IMPORTANT NAMES & ENTITIES:
REFERENCE NUMBERS:
FINAL VERIFICATION RECOMMENDATION:
"""

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    if len(base64_images) > 0:
        model_to_use = "qwen/qwen3.6-27b"
        content_payload = [{"type": "text", "text": prompt}]
        for b64 in base64_images:
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
            })
        messages = [{"role": "user", "content": content_payload}]
    else:
        model_to_use = "openai/gpt-oss-20b"
        messages = [
            {"role": "system", "content": "You are a professional document verification assistant. Only output the requested template."},
            {"role": "user", "content": prompt}
        ]

    data = {
        "model": model_to_use,
        "messages": messages,
        "temperature": 0.1
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=120)
        
        if response.status_code != 200:
            return {"success": False, "error": f"API request failed with code {response.status_code}."}

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            answer = result["choices"][0]["message"]["content"]
            
            # Safely remove <think> tags
            answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
            
            # Chop off any rambling intro text
            if "AUTHENTICITY & TAMPER ASSESSMENT:" in answer:
                answer = "AUTHENTICITY & TAMPER ASSESSMENT:" + answer.split("AUTHENTICITY & TAMPER ASSESSMENT:")[1]
                
            return {"success": True, "analysis": answer.strip()}
        else:
            return {"success": False, "error": "Invalid response format from AI."}

    except Exception as error:
        return {"success": False, "error": str(error)}

# ==========================================================
# ROUTES
# ==========================================================
@app.route("/")
def home():
    return render_template("index.html", result=latest_result)

@app.route("/verify", methods=["GET", "POST"])
def verify():
    global latest_result

    if request.method == "GET":
        return render_template("index.html", result=latest_result)

    if "document" not in request.files:
        latest_result = {"filename": "", "analysis": "", "status": "ERROR", "error": "No document was uploaded."}
        return redirect(url_for("result_page"))

    file = request.files["document"]

    if file.filename == "":
        latest_result = {"filename": "", "analysis": "", "status": "ERROR", "error": "Please select a document."}
        return redirect(url_for("result_page"))

    filename = file.filename
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    extension = filename.lower().split(".")[-1]
    
    if extension == "pdf":
        document_text, metadata_info, base64_images = extract_pdf_data(file_path)
    elif extension == "txt":
        document_text, metadata_info, base64_images = extract_txt_text(file_path)
    else:
        latest_result = {"filename": filename, "analysis": "", "status": "ERROR", "error": "Only PDF and TXT files are supported."}
        return redirect(url_for("result_page"))

    if not document_text.strip() and not base64_images:
        latest_result = {"filename": filename, "analysis": "", "status": "ERROR", "error": "No readable text or images found in document."}
        return redirect(url_for("result_page"))

    groq_result = analyze_forgery_and_content(document_text, metadata_info, base64_images)
    if groq_result["success"]:
        latest_result = {
            "filename": filename,
            "analysis": groq_result["analysis"],
            "status": "VERIFIED & ANALYZED",
            "error": ""
        }
    else:
        latest_result = {
            "filename": filename,
            "analysis": "",
            "status": "ERROR",
            "error": groq_result.get("error", "Verification failed.")
        }

    return redirect(url_for("result_page"))

@app.route("/result")
def result_page():
    return render_template("index.html", result=latest_result)

@app.route("/about")
def about():
    return render_template("index.html", result=latest_result)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)