# guardrails.py

OFF_TOPIC_KEYWORDS = [
    "cricket", "recipe", "weather", "politics", "invest",
    "stock", "relationship", "health advice", "medical"
]

PERSONAL_ADVICE_PATTERNS = [
    "should i sue", "will i win", "am i eligible",
    "can i get compensation", "what should i do"
]

SENSITIVE_PATTERNS = [
    "how to avoid paying", "hide salary", "fire without",
    "avoid eobi", "underpay"
]

def check_input(query):
    q = query.lower()
    
    for kw in OFF_TOPIC_KEYWORDS:
        if kw in q:
            return "off_topic", "This assistant only answers Pakistan labour law questions."
    
    for p in SENSITIVE_PATTERNS:
        if p in q:
            return "harmful", "This assistant cannot help with requests that may facilitate worker rights violations."
    
    for p in PERSONAL_ADVICE_PATTERNS:
        if p in q:
            return "personal_advice", None  # Allow but flag — LLM will handle with disclaimer
    
    return "ok", None


def check_output(response):
    """Post-generation checks"""
    issues = []
    
    # Check disclaimer is present
    if "DISCLAIMER" not in response:
        response_text = response.choices[0].message.content
        response_text += "\n\nDISCLAIMER: This information is for general awareness only and does not constitute legal advice."
        response = response_text    
        issues.append("disclaimer_added")
    
    # Check for hallucination red flags — years that don't exist in corpus
    import re
    years = re.findall(r'\b(19[0-9]{2}|20[0-9]{2})\b', response)
    valid_years = {1923, 1934, 1936, 1958, 1961, 1968, 1969, 1976, 1992, 1991,
                   2010, 2012, 2013, 2015, 2018, 2019, 2021, 2022, 2023, 2024, 2025}
    for y in years:
        if int(y) not in valid_years:
            issues.append(f"suspicious_year_{y}")
    
    return response, issues