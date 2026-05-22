import os
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, func, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from .config import settings

# --- SQLAlchemy Setup ---
# Updated to support PostgreSQL with pooling and pre-ping
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Models ---

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="doctor")
    is_verified = Column(Boolean, default=False)
    lab_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PendingUser(Base):
    __tablename__ = "pending_users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    lab_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class OTP(Base):
    __tablename__ = "otps"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    otp_code = Column(String, nullable=False)
    purpose = Column(String, nullable=False) # 'register', 'forgot_password'
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class DiagnosticTest(Base):
    __tablename__ = "diagnostic_tests"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    cancer_type = Column(String, nullable=False)
    genes = Column(String, nullable=False)
    lab = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    test_id = Column(Integer, nullable=False)
    patient_name = Column(String, nullable=False)
    lab_name = Column(String, nullable=True)
    contact = Column(String, nullable=False)
    status = Column(String, default="Placed")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# --- Dependency ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Connection Management ---

import psycopg2.extras
from sqlalchemy import text

@contextmanager
def get_raw_db_conn():
    """
    Context manager for raw database connections using SQLAlchemy's raw_connection.
    Provides DictCursor for PostgreSQL to maintain row["column"] compatibility.
    """
    conn = engine.raw_connection()
    try:
        # If it's a PostgreSQL connection, use DictCursor
        if hasattr(conn, "cursor_factory"):
            conn.cursor_factory = psycopg2.extras.DictCursor
        yield conn
    finally:
        conn.close()


def seed_users():
    """Seeds mock users for each role if they don't exist."""
    from .auth.service import get_password_hash
    db = SessionLocal()
    try:
        mock_users = [
            {"name": "Doctor User", "email": "doctor@test.com", "password": "doctor123", "role": "doctor"},
            {"name": "Coordinator User", "email": "coordinator@test.com", "password": "coordinator123", "role": "coordinator"},
            {"name": "Admin User", "email": "admin@test.com", "password": "admin123", "role": "admin"},
            {"name": "ABC Lab User", "email": "abclab@test.com", "password": "abc123", "role": "lab", "lab_name": "ABC Labs"},
            {"name": "XYZ Lab User", "email": "xyzlab@test.com", "password": "xyz123", "role": "lab", "lab_name": "XYZ Labs"},
        ]

        
        for u in mock_users:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if not existing:
                new_user = User(
                    name=u["name"],
                    email=u["email"],
                    password_hash=get_password_hash(u["password"]),
                    role=u["role"],
                    lab_name=u.get("lab_name"),
                    is_verified=True
                )

                db.add(new_user)
                print(f"[DB] Seeding user: {u['email']} ({u['role']})")
        db.commit()
    except Exception as e:
        print(f"[DB] Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()


def seed_diagnostic_tests():
    """Seeds the diagnostic_tests table with mock data using SQLAlchemy."""
    db = SessionLocal()
    try:
        # Check if any tests exist to avoid duplicates
        existing = db.query(DiagnosticTest).first()
        if existing:
            return

        tests_data = [
             {"name": "Lung Cancer Panel", "cancer_type": "Lung Cancer", "genes": "EGFR, ALK, KRAS, ROS1, BRAF", "lab": "XYZ Labs", "price": 25000},
    {"name": "Targeted EGFR Test", "cancer_type": "Lung Cancer", "genes": "EGFR", "lab": "ABC Labs", "price": 12000},
    {"name": "Breast Cancer Panel", "cancer_type": "Breast Cancer", "genes": "BRCA1, BRCA2, HER2, PIK3CA, TP53", "lab": "ABC Labs", "price": 28000},
    {"name": "BRCA Mutation Test", "cancer_type": "Breast / Ovarian Cancer", "genes": "BRCA1, BRCA2", "lab": "XYZ Labs", "price": 18000},
    {"name": "Colon Cancer Panel", "cancer_type": "Colorectal Cancer", "genes": "KRAS, NRAS, BRAF, APC, TP53", "lab": "ABC Labs", "price": 24000},
    {"name": "Leukemia Panel", "cancer_type": "Blood Cancer", "genes": "FLT3, NPM1, CEBPA, JAK2", "lab": "XYZ Labs", "price": 26000},
    {"name": "Prostate Cancer Panel", "cancer_type": "Prostate Cancer", "genes": "BRCA1, BRCA2, ATM, HOXB13", "lab": "ABC Labs", "price": 23000},
    {"name": "Ovarian Cancer Panel", "cancer_type": "Ovarian Cancer", "genes": "BRCA1, BRCA2, RAD51C, TP53", "lab": "XYZ Labs", "price": 27000},
    {"name": "Melanoma Panel", "cancer_type": "Skin Cancer", "genes": "BRAF, NRAS, KIT", "lab": "ABC Labs", "price": 21000},
    {"name": "Pancreatic Cancer Panel", "cancer_type": "Pancreatic Cancer", "genes": "KRAS, CDKN2A, TP53, SMAD4", "lab": "XYZ Labs", "price": 29000},
    {"name": "Thyroid Cancer Panel", "thyroid_cancer": "Thyroid Cancer", "genes": "BRAF, RET, RAS, TERT", "lab": "ABC Labs", "price": 22000},
    {"name": "Liver Cancer Panel", "cancer_type": "Liver Cancer", "genes": "TP53, CTNNB1, AXIN1", "lab": "XYZ Labs", "price": 25000},
    {"name": "Kidney Cancer Panel", "cancer_type": "Kidney Cancer", "genes": "VHL, PBRM1, SETD2, BAP1", "lab": "ABC Labs", "price": 24500},
    {"name": "Brain Tumor Panel", "cancer_type": "Brain Cancer", "genes": "IDH1, IDH2, EGFR, TP53, ATRX", "lab": "XYZ Labs", "price": 32000},
    {"name": "Cervical Cancer Panel", "cancer_type": "Cervical Cancer", "genes": "PIK3CA, PTEN, TP53", "lab": "ABC Labs", "price": 21500},
        ]

        # Fix any potential key issues
        for test in tests_data:
            if "thyroid_cancer" in test:
                test["cancer_type"] = test.pop("thyroid_cancer")

        for t in tests_data:
            new_test = DiagnosticTest(**t)
            db.add(new_test)
        
        db.commit()
        print("[DB] Diagnostic tests seeded successfully")
    except Exception as e:
        print(f"[DB] Error seeding tests: {e}")
        db.rollback()
    finally:
        db.close()


def init_db():
    """Initializes all tables using SQLAlchemy models and handles migrations."""
    # This creates all tables defined as SQLAlchemy models
    Base.metadata.create_all(bind=engine)
    
    # Migration-safe logic to add 'role' column to 'users' table if it doesn't exist
    # This works for both SQLite and PostgreSQL
    with engine.connect() as conn:
        try:
            # Check if role column exists
            # Using text() for raw SQL compatibility across DBs
            if "sqlite" in str(engine.url):
                # SQLite check
                cursor = conn.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in cursor]
            else:
                # PostgreSQL check
                cursor = conn.execute(text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='users'"
                ))
                columns = [row[0] for row in cursor]

            if "role" not in columns:
                print("[DB] Adding 'role' column to 'users' table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR NOT NULL DEFAULT 'doctor'"))
                conn.commit()

            if "lab_name" not in columns:
                print("[DB] Adding 'lab_name' column to 'users' table...")
                conn.execute(text("ALTER TABLE users ADD COLUMN lab_name VARCHAR"))
                conn.commit()
        except Exception as e:
            print(f"[DB] Migration notice: {e}")


    # Seed mock users and diagnostic tests
    seed_users()
    seed_diagnostic_tests()
    
    print("[DB] Database initialized successfully.")

