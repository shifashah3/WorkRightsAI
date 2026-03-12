# import os

# DATA_FOLDER = "data"  # change this to your actual folder path

# print("=" * 60)
# print("PDF AUDIT REPORT")
# print("=" * 60)

# total = 0
# for folder in os.listdir(DATA_FOLDER):
#     folder_path = os.path.join(DATA_FOLDER, folder)
#     if os.path.isdir(folder_path):
#         pdfs = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]
#         print(f"\n📁 {folder} ({len(pdfs)} files)")
#         for pdf in pdfs:
#             size = os.path.getsize(os.path.join(folder_path, pdf))
#             print(f"   - {pdf} ({round(size/1024)}KB)")
#         total += len(pdfs)

# print(f"\nTotal PDFs: {total}")



import pdfplumber
import os

DATA_FOLDER = "data"  # change to your path

print("=" * 60)
print("TEXT EXTRACTION CHECK")
print("=" * 60)

for folder in os.listdir(DATA_FOLDER):
    folder_path = os.path.join(DATA_FOLDER, folder)
    if not os.path.isdir(folder_path):
        continue
    
    print(f"\n📁 {folder}")
    
    for fname in os.listdir(folder_path):
        if not fname.endswith(".pdf"):
            continue
        
        fpath = os.path.join(folder_path, fname)
        try:
            with pdfplumber.open(fpath) as pdf:
                # Check first 3 pages
                text_found = 0
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text and len(text.strip()) > 50:
                        text_found += 1
                
                if text_found >= 2:
                    status = "✅ TEXT OK"
                elif text_found == 1:
                    status = "⚠️  PARTIAL"
                else:
                    status = "❌ SCANNED (needs OCR)"
        except Exception as e:
            status = f"❌ ERROR: {str(e)}"
        
        print(f"   {status} — {fname}")