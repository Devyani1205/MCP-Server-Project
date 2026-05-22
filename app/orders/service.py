from ..database import SessionLocal, Order, DiagnosticTest, User, get_db
from sqlalchemy import func
import logging

logger = logging.getLogger(__name__)

def get_test_by_id(test_id: int):
    """Fetches diagnostic test details from DB using SQLAlchemy."""
    db_gen = get_db()
    db = next(db_gen)
    try:
        test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            return None
        return {
            "id": test.id,
            "name": test.name,
            "lab": test.lab,
            "price": test.price
        }
    finally:
        db_gen.close()

def generate_order_id():
    """Generates a sequential order ID (e.g., ORD1001) using SQLAlchemy."""
    db_gen = get_db()
    db = next(db_gen)
    try:
        count = db.query(func.count(Order.id)).scalar()
        next_id = 1001 + count
        return f"ORD{next_id}"
    finally:
        db_gen.close()

def place_order(user_id: int, test_id: int, patient_name: str, contact: str, lab_name: str = None):
    """
    Inserts a new order into the database with robust lab name validation.
    Handles case-sensitivity and extra spaces to avoid strict matching failures.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        # 1. Validate test exists
        test = db.query(DiagnosticTest).filter(DiagnosticTest.id == test_id).first()
        if not test:
            raise ValueError(f"Diagnostic test with ID {test_id} not found")

        # 2. Normalize input for matching
        if not lab_name:
            raise ValueError("Lab name must be provided")
        
        search_term = lab_name.strip()
        normalized_search = search_term.lower()

        # 3. Robust Lab Lookup (Case-insensitive & Trimmed)
        # We first try exact normalized match on lab_name
        lab_user = db.query(User).filter(
            User.role == "lab",
            func.lower(func.trim(User.lab_name)) == normalized_search
        ).first()

        # Fallback: Try partial match if exact normalized match fails
        if not lab_user:
            lab_user = db.query(User).filter(
                User.role == "lab",
                User.lab_name.ilike(f"%{search_term}%")
            ).first()

        if not lab_user:
            raise ValueError(f"The lab '{lab_name}' is not registered in our system. Please check the name and try again.")

        # Use the CANONICAL lab name from the database record
        canonical_lab_name = lab_user.lab_name

        # 4. Validate Lab/Test Mapping
        # Both test.lab and canonical_lab_name should match (normalized)
        if test.lab.strip().lower() != canonical_lab_name.strip().lower():
            raise ValueError(f"Test '{test.name}' is only available at '{test.lab}', but you specified '{canonical_lab_name}'")

        order_id = generate_order_id()
        
        new_order = Order(
            order_id=order_id,
            user_id=user_id,
            test_id=test_id,
            patient_name=patient_name,
            lab_name=canonical_lab_name, # Store canonical name
            contact=contact,
            status="Placed"
        )
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return order_id
    except Exception as e:
        db.rollback()
        logger.error(f"Order Placement Error: {str(e)}")
        raise e
    finally:
        db_gen.close()
def get_user_orders(user_id: int):
    """
    Fetches all orders for a specific user with joined test details using SQLAlchemy.
    Sorted newest first.
    """
    db_gen = get_db()
    db = next(db_gen)
    try:
        # Query with join
        results = db.query(Order, DiagnosticTest).join(
            DiagnosticTest, Order.test_id == DiagnosticTest.id
        ).filter(
            Order.user_id == user_id
        ).order_by(
            Order.created_at.desc()
        ).all()
        
        orders = []
        for order, test in results:
            orders.append({
                "order_id": order.order_id,
                "patient_name": order.patient_name,
                "lab_name": order.lab_name,
                "contact": order.contact,
                "status": order.status,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "test": {
                    "test_id": test.id,
                    "name": test.name,
                    "lab": test.lab,
                    "price": test.price
                }
            })
        return orders
    finally:
        db_gen.close()
