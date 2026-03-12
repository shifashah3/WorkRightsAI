import pdfplumber
import json
import os
import re

DATA_FOLDER = "data"
OCR_FOLDER = "data_ocr"
OUTPUT_FILE = "extracted_chunks.json"

# Metadata for each file
FILE_METADATA = {
    # Federal
    "BONDED LABOUR SYSTEM (ABOLITION) ACT,1992.pdf": {"province": "Federal", "law": "Bonded Labour System (Abolition) Act", "year": 1992},
    "Employment of Children Act.pdf": {"province": "Federal", "law": "Employment of Children Act", "year": 1991},
    "Industrial Relations Act.pdf": {"province": "Federal", "law": "Industrial Relations Act", "year": 2012},
    "Minimum Wages Ordinance.pdf": {"province": "Federal", "law": "Minimum Wages Ordinance", "year": 1961},
    "Payment of Wages Act.pdf": {"province": "Federal", "law": "Payment of Wages Act", "year": 1936},
    "THE EMPLOYEES OLD AGE BENEFIT ACT.pdf": {"province": "Federal", "law": "Employees Old Age Benefits Act", "year": 1976},
    "THE FACTORIES ACT, 1934.pdf": {"province": "Federal", "law": "Factories Act", "year": 1934},
    "THE MINES ACT, 1923.pdf": {"province": "Federal", "law": "Mines Act", "year": 1923},
    "THE PROTECTION AGAINST HARASSMENT OF WOMEN ATTHE WORKPLACE ACT, 2010.pdf": {"province": "Federal", "law": "Protection Against Harassment of Women at Workplace Act", "year": 2010},
    "THE WEST PAKISTAN SHOPS AND ESTABLISHMENTSORDINANCE, 1969 .pdf": {"province": "Federal", "law": "West Pakistan Shops and Establishments Ordinance", "year": 1969},
    "THE WORKMEN'S COMPENSATION ACT, 1923.pdf": {"province": "Federal", "law": "Workmen's Compensation Act", "year": 1923},
    "THE WEST PAKISTAN MATERNITY BENEFIT ORDINANCE,1958.pdf": {"province": "Federal", "law": "Maternity Benefit Ordinance", "year": 1958},
    # Punjab
    "39-industrial-and-commercial-employment-standing-orders-ordinance-1968-vi-of-1968-pdf.pdf": {"province": "Punjab", "law": "Industrial and Commercial Employment Standing Orders Ordinance", "year": 1968},
    "Minimum Rates of Wages Notification Punjab 2024-25 Dt; 06-09-2024-1.pdf": {"province": "Punjab", "law": "Minimum Wages Notification", "year": 2024},
    "THE PUNJAB SHOPS AND ESTABLISHMENTS ORDINANCE, 1969.pdf": {"province": "Punjab", "law": "Punjab Shops and Establishments Ordinance", "year": 1969},
    "the-punjab-domestic-workers-act-2019-pdf.pdf": {"province": "Punjab", "law": "Punjab Domestic Workers Act", "year": 2019},
    "THE_PUNJAB_INDUSTRIAL_RELATIONS_ACT_2010.doc.pdf": {"province": "Punjab", "law": "Punjab Industrial Relations Act", "year": 2010},
    # Sindh
    "Sindh Home Based Workers Act 2018.pdf": {"province": "Sindh", "law": "Sindh Home Based Workers Act", "year": 2018},
    "Sindh Industrial Relation Act, 2013.pdf": {"province": "Sindh", "law": "Sindh Industrial Relations Act", "year": 2013},
    "Sindh Shops and Commercial Estalishment Act 2015.pdf": {"province": "Sindh", "law": "Sindh Shops and Commercial Establishment Act", "year": 2015},
    "Sindh-Minimum-Wage-Notification-Un-Skilled-2024-25-1.pdf": {"province": "Sindh", "law": "Sindh Minimum Wage Notification (Unskilled)", "year": 2024},
    "Skilled-Workers-Minimum-wages-25-26_compressed.pdf": {"province": "Sindh", "law": "Sindh Minimum Wage Notification (Skilled)", "year": 2025},
    "THE PROTECTION AGAINST HARASSMENT OF WOMEN AT THEWORKPLACE ACT 2010.pdf": {"province": "Sindh", "law": "Protection Against Harassment of Women at Workplace Act", "year": 2010},
    "THE SINDH MINIMUM WAGES ACT, 2015.pdf": {"province": "Sindh", "law": "Sindh Minimum Wages Act", "year": 2015},
    "THE SINDH TERMS OF EMPLOYMENT (STANDING ORDERS) ACT, 2015.pdf": {"province": "Sindh", "law": "Sindh Terms of Employment (Standing Orders) Act", "year": 2015},
    # KPK
    "2013_11_THE_KHYBER_PAKHTUNKHWA_INDUSTRIAL_AND_COMMERCIAL_EMPLOYMENT_STANDING_ORDERS_ACT_2013.pdf": {"province": "KPK", "law": "KPK Industrial and Commercial Employment Standing Orders Act", "year": 2013},
    "KPK-Minimum-Wages-Notification-2025.pdf": {"province": "KPK", "law": "KPK Minimum Wages Notification", "year": 2025},
    "the_Khyber_Pakhtunkhwa_Industrial_Relations_Act,_2010.pdf": {"province": "KPK", "law": "KPK Industrial Relations Act", "year": 2010},
    "THE_KHYBER_PAKHTUNKHWA_PAYMENT_OF_WAGES_ACT_20131.pdf": {"province": "KPK", "law": "KPK Payment of Wages Act", "year": 2013},
    "THE_KHYBER_PAKHTUNKHWA_SHOPS_AND_ESTABLISHMENT_ACT_2015.pdf": {"province": "KPK", "law": "KPK Shops and Establishment Act", "year": 2015},
    # Balochistan
    "Balochistan Minimum Wage Notification 2023.pdf": {"province": "Balochistan", "law": "Balochistan Minimum Wage Notification", "year": 2023},
    "Balochistan Payment of Wages Act, 2021.pdf": {"province": "Balochistan", "law": "Balochistan Payment of Wages Act", "year": 2021},
    "THE BALOCHISTAN INDUSTRIAL DEVELOPMENT ANDREGULATIONS ACT, 2025.pdf": {"province": "Balochistan", "law": "Balochistan Industrial Development and Regulations Act", "year": 2025},
    "THE BALOCHISTAN INDUSTRIAL RELATIONS ACT, 2022.pdf": {"province": "Balochistan", "law": "Balochistan Industrial Relations Act", "year": 2022},
}

# Files that came from OCR (map original pdf name to ocr txt file)
OCR_MAP = {
    "Balochistan Minimum Wage Notification 2023.pdf": "Balochistan Minimum Wage Notification 2023_ocr.txt",
    "Balochistan Payment of Wages Act, 2021.pdf": "Balochistan Payment of Wages Act, 2021_ocr.txt",
    "THE BALOCHISTAN INDUSTRIAL RELATIONS ACT, 2022.pdf": "THE BALOCHISTAN INDUSTRIAL RELATIONS ACT, 2022_ocr.txt",
    "Employment of Children Act.pdf": "Employment of Children Act_ocr.txt",
    "Industrial Relations Act.pdf": "Industrial Relations Act_ocr.txt",
    "KPK-Minimum-Wages-Notification-2025.pdf": "KPK-Minimum-Wages-Notification-2025_ocr.txt",
    "Sindh-Minimum-Wage-Notification-Un-Skilled-2024-25-1.pdf": "Sindh-Minimum-Wage-Notification-Un-Skilled-2024-25-1_ocr.txt",
    "Skilled-Workers-Minimum-wages-25-26_compressed.pdf": "Skilled-Workers-Minimum-wages-25-26_compressed_ocr.txt",
}

def clean_text(text):
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove page markers
    text = re.sub(r'\[PAGE_\d+\]', '', text)
    return text.strip()

def split_into_sections(text):
    """Split by section numbers — handles most Pakistani legal doc formats"""
    pattern = re.compile(
        r'(?=\n\s*(?:Section|SECTION|section)?\s*(\d+[A-Z]?)\s*[\.\-\)]\s*[A-Z])',
        re.MULTILINE
    )
    parts = pattern.split(text)
    
    sections = []
    i = 0
    while i < len(parts):
        chunk = parts[i].strip()
        if len(chunk) > 150:
            sections.append(chunk)
        i += 1
    
    # If no sections found, chunk by paragraphs
    if len(sections) <= 1:
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 150]
        return paragraphs
    
    return sections

def get_section_number(text):
    match = re.match(r'^(?:Section|SECTION)?\s*(\d+[A-Z]?)[\.\-\)]\s', text.strip())
    return match.group(1) if match else None

def get_text_from_pdf(fpath):
    full_text = ""
    with pdfplumber.open(fpath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                full_text += f"\n[PAGE_{i+1}]\n{text}"
    return full_text

def get_text_from_ocr(ocr_filename):
    fpath = os.path.join(OCR_FOLDER, ocr_filename)
    with open(fpath, "r", encoding="utf-8") as f:
        return f.read()

# Main extraction
all_chunks = []

for folder in os.listdir(DATA_FOLDER):
    folder_path = os.path.join(DATA_FOLDER, folder)
    if not os.path.isdir(folder_path):
        continue

    for fname in os.listdir(folder_path):
        if not fname.endswith(".pdf"):
            continue

        meta = FILE_METADATA.get(fname)
        if not meta:
            print(f"⚠️  No metadata for: {fname} — skipping")
            continue

        print(f"Extracting: {fname}")

        # Get text from OCR or direct PDF
        if fname in OCR_MAP:
            raw_text = get_text_from_ocr(OCR_MAP[fname])
            source = "ocr"
        else:
            raw_text = get_text_from_pdf(os.path.join(folder_path, fname))
            source = "pdf"

        cleaned = clean_text(raw_text)
        sections = split_into_sections(cleaned)

        for idx, section_text in enumerate(sections):
            sec_num = get_section_number(section_text) or str(idx + 1)
            chunk_id = f"{meta['province'].lower()}_{meta['year']}_{meta['law'][:20].replace(' ', '_')}_{sec_num}"

            all_chunks.append({
                "chunk_id": chunk_id,
                "province": meta["province"],
                "law": meta["law"],
                "year": meta["year"],
                "section_number": sec_num,
                "text": section_text[:3000],
                "source_file": fname,
                "source_type": source
            })

        print(f"  → {len(sections)} sections extracted")

# Save
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(all_chunks, f, ensure_ascii=False, indent=2)

print(f"\n✅ Done. Total chunks: {len(all_chunks)}")
print(f"Saved to {OUTPUT_FILE}")


# FIXING KPK MINIMUM WAGE CHUNK (garbage OCR) — also adding a new dedicated chunk for the wage table for better retrieval in chatbot

# import json

# with open("extracted_chunks.json", "r", encoding="utf-8") as f:
#     chunks = json.load(f)

# # Fix the garbage OCR chunk
# for chunk in chunks:
#     if chunk["law"] == "KPK Minimum Wages Notification" and chunk["section_number"] == "1":
#         chunk["text"] = """GOVERNMENT OF KHYBER PAKHTUNKHWA
# LABOUR DEPARTMENT
# NOTIFICATION
# Peshawar, Dated 10/09/2025

# In exercise of the powers conferred by clause (ii) of sub-section (1) of section 6 of the 
# Khyber Pakhtunkhwa Minimum Wages Act, 2013, the Government of Khyber Pakhtunkhwa 
# hereby revises the minimum wages for workers in industrial and commercial establishments in KPK.

# MINIMUM WAGES TABLE (Effective 2025):

# Category: Adult, unskilled, juvenile and adolescent workers employed in industrial 
# and commercial establishments, whether registered or unregistered, located in the 
# Province of Khyber Pakhtunkhwa.

# Minimum Rates of Wages:
# - Per day (8 hours of work): Rs. 1,538.46
# - Per month (26 working days): Rs. 40,000

# (Rupees Forty Thousand only per month)"""
#         print("✅ Fixed KPK chunk 1")

# # Also add as a separate dedicated chunk for better retrieval
# new_chunk = {
#     "chunk_id": "kpk_2025_minimum_wage_table_manual",
#     "province": "KPK",
#     "law": "KPK Minimum Wages Notification",
#     "year": 2025,
#     "section_number": "table",
#     "text": """KPK Minimum Wage 2025 - Khyber Pakhtunkhwa Minimum Wages Notification

# The Government of Khyber Pakhtunkhwa has set the following minimum wages effective 2025:

# Category: All adult, unskilled, juvenile and adolescent workers in industrial and 
# commercial establishments in Khyber Pakhtunkhwa (KPK).

# Minimum wage rates:
# - Daily rate (8 hours): Rs. 1,538.46 per day
# - Monthly rate (26 working days): Rs. 40,000 per month

# No employer in KPK may pay below these rates. Existing wages higher than minimum 
# wages shall not be reduced.""",
#     "source_file": "KPK-Minimum-Wages-Notification-2025.pdf",
#     "source_type": "manual_correction"
# }

# chunks.append(new_chunk)
# print("✅ Added dedicated wage table chunk")

# with open("extracted_chunks.json", "w", encoding="utf-8") as f:
#     json.dump(chunks, f, ensure_ascii=False, indent=2)

# print(f"✅ Saved. Total chunks: {len(chunks)}")