import re

def parse_query(query: str) -> dict:
    """
    Improved keyword-based parser for diagnostic queries.
    Detects cancer types and specific genes.
    """
    query_lower = query.lower()
    parsed_data = {
        "cancer_type": None,
        "gene": None,
        "is_generic": False
    }

    # Detect Cancer Types
    cancer_types = [
        "lung", "breast", "ovarian", "colorectal", "colon", "blood", "leukemia",
        "prostate", "skin", "melanoma", "pancreatic", "thyroid", "liver", "kidney", 
        "brain", "cervical"
    ]
    
    for c_type in cancer_types:
        if c_type in query_lower:
            # Map 'colon' to 'Colorectal' for DB match if needed, but let's keep it simple
            parsed_data["cancer_type"] = c_type.capitalize()
            break

    # Detect Genes (common ones from our list)
    genes = [
        "EGFR", "ALK", "KRAS", "ROS1", "BRAF", "BRCA1", "BRCA2", "HER2", 
        "PIK3CA", "TP53", "NRAS", "APC", "FLT3", "NPM1", "CEBPA", "JAK2",
        "ATM", "HOXB13", "RAD51C", "CDKN2A", "SMAD4", "RET", "RAS", "TERT",
        "CTNNB1", "AXIN1", "VHL", "PBRM1", "SETD2", "BAP1", "IDH1", "IDH2",
        "ATRX", "PTEN"
    ]
    
    for gene in genes:
        if gene.lower() in query_lower:
            parsed_data["gene"] = gene
            break

    # Generic query check
    generic_keywords = ["diagnostic", "recommendation", "test", "panel", "all", "list"]
    if any(keyword in query_lower for keyword in generic_keywords) and not parsed_data["cancer_type"] and not parsed_data["gene"]:
        parsed_data["is_generic"] = True

    return parsed_data
