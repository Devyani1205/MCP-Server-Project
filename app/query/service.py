from .parser import parse_query
from ..ai.groq_provider import groq_provider
from ..database import get_db, DiagnosticTest
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_tests_from_db(parsed_data: dict) -> list:
    """
    Fetches matching diagnostic tests from the PostgreSQL database using SQLAlchemy.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        query = db.query(DiagnosticTest)
        
        # Matching Logic using ILIKE for PostgreSQL case-insensitive search
        if parsed_data.get("gene"):
            query = query.filter(DiagnosticTest.genes.ilike(f"%{parsed_data['gene']}%"))
        
        if parsed_data.get("cancer_type"):
            query = query.filter(DiagnosticTest.cancer_type.ilike(f"%{parsed_data['cancer_type']}%"))
        
        # If no specific filters, and we want to be safe, we could limit results or use a general search
        # For now, following the parsed data logic.
        
        tests = query.all()
        
        # Convert SQLAlchemy objects to dictionaries
        return [
            {
                "test_id": t.id,
                "name": t.name,
                "cancer_type": t.cancer_type,
                "genes": t.genes,
                "lab": t.lab,
                "price": t.price
            }
            for t in tests
        ]
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        return []
    finally:
        db_gen.close()

def process_diagnostic_query(query: str) -> dict:
    """
    Full pipeline: Parse -> Database Match -> AI Recommend
    """
    try:
        parsed = parse_query(query)
        matched = get_tests_from_db(parsed)
        
        if not matched:
            return {
                "query": query,
                "tests": [], # Consistent with user requested field name
                "message": "No matching tests found"
            }

        ai_suggestion = "AI recommendation temporarily unavailable"
        try:
            ai_suggestion = groq_provider.get_recommendation(query, matched)
        except Exception as ai_err:
            logger.error(f"AI recommendation failed: {ai_err}")

        return {
            "query": query,
            "tests": matched,
            "ai_suggestion": ai_suggestion
        }
    except Exception as e:
        logger.error(f"[ERROR] query_tests failed: {e}")
        return {
            "query": query,
            "tests": [],
            "error": "Query failed due to an internal server error"
        }
