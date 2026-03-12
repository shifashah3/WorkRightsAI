import pdfplumber
import pytesseract
from pdf2image import convert_from_path
import os


DATA_FOLDER = "data"

SCANNED_FILES = [
    "Balochistan/Balochistan Minimum Wage Notification 2023.pdf",
    "Balochistan/Balochistan Payment of Wages Act, 2021.pdf",
    "Balochistan/THE BALOCHISTAN INDUSTRIAL RELATIONS ACT, 2022.pdf",
    "Federal Laws/Employment of Children Act.pdf",
    "Federal Laws/Industrial Relations Act.pdf",
    "KPK/KPK-Minimum-Wages-Notification-2025.pdf",
    "Sindh/Sindh-Minimum-Wage-Notification-Un-Skilled-2024-25-1.pdf",
    "Sindh/Skilled-Workers-Minimum-wages-25-26_compressed.pdf",
]

OUTPUT_FOLDER = "data_ocr"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for relative_path in SCANNED_FILES:
    full_path = os.path.join(DATA_FOLDER, relative_path)
    fname = os.path.basename(relative_path)
    out_path = os.path.join(OUTPUT_FOLDER, fname.replace(".pdf", "_ocr.txt"))
    
    print(f"Processing: {fname}")
    
    try:
        pages = convert_from_path(full_path, dpi=300)
        full_text = ""
        
        for i, page_img in enumerate(pages):
            # Try English first, add 'urd' if you have Urdu tesseract pack
            text = pytesseract.image_to_string(page_img, lang='eng')
            full_text += f"\n[PAGE_{i+1}]\n{text}"
            print(f"  Page {i+1}/{len(pages)} done")
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"  ✅ Saved to {out_path}\n")
    
    except Exception as e:
        print(f"  ❌ Failed: {e}\n")

print("OCR complete. Check data_ocr/ folder.")