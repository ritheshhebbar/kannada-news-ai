import base64
import io
import json
import logging
import os
import re
import urllib.request
from typing import Optional

import pypdf

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for extracting text from PDFs, plain text, and news images/e-papers via OCR."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()

    def extract_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extracts text from a digital or scanned PDF document."""
        if not pdf_bytes:
            return ""

        extracted_text = []
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
            for page_idx, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    extracted_text.append(text.strip())

            full_text = "\n\n".join(extracted_text).strip()
            
            # If digital text extraction yielded sufficient content, return it
            if len(full_text) >= 60:
                logger.info("Successfully extracted %d characters from digital PDF (%d pages)", len(full_text), len(reader.pages))
                return full_text

            # If digital text was sparse, try OCR on embedded page images
            logger.info("PDF has sparse digital text (%d chars). Attempting OCR on page images...", len(full_text))
            ocr_text = []
            for page_idx, page in enumerate(reader.pages[:5]):  # limit first 5 pages for responsiveness
                for img_file in page.images:
                    img_data = img_file.data
                    txt = self.extract_from_image(img_data, mime_type="image/png")
                    if txt.strip():
                        ocr_text.append(txt.strip())

            if ocr_text:
                return "\n\n".join(ocr_text).strip()

            return full_text

        except Exception as e:
            logger.error("Failed to parse PDF bytes: %s", e)
            return ""

    def extract_from_image(self, image_bytes: bytes, mime_type: str = "image/png") -> str:
        """Extracts text from e-paper clippings or news screenshots using Gemini Vision OCR."""
        if not image_bytes:
            return ""

        if not self.api_key:
            logger.warning("No GEMINI_API_KEY configured for Image OCR.")
            return ""

        # Normalize mime type
        if "jpg" in mime_type.lower() or "jpeg" in mime_type.lower():
            norm_mime = "image/jpeg"
        elif "webp" in mime_type.lower():
            norm_mime = "image/webp"
        else:
            norm_mime = "image/png"

        b64_data = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "You are an expert Kannada news OCR engine. Extract all Kannada news text "
            "from this document / e-paper image accurately. "
            "Output only the extracted text with proper line and paragraph breaks. "
            "Do not include commentary, explanations, or markdown code fences."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"inline_data": {"mime_type": norm_mime, "data": b64_data}}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
            }
        }

        models = ["gemini-3.1-flash-lite", "gemini-3-flash-preview"]
        for model in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            try:
                data = json.dumps(payload).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=20) as resp:
                    resp_json = json.loads(resp.read().decode("utf-8"))
                    text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    # Clean markdown wrappers if any
                    text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                    if text:
                        return text
            except Exception as e:
                logger.warning("Gemini Vision OCR with model %s failed: %s", model, e)

        return ""

    def extract_from_txt(self, txt_bytes: bytes) -> str:
        """Extracts text from plain text file bytes."""
        for enc in ["utf-8", "utf-8-sig", "utf-16", "latin-1"]:
            try:
                return txt_bytes.decode(enc).strip()
            except Exception:
                continue
        return ""

document_service = DocumentService()

