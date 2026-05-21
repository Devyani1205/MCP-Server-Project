from app.database import init_db, seed_diagnostic_tests

if __name__ == "__main__":
    # 1. Create tables and seed (init_db calls seed_users and seed_diagnostic_tests)
    init_db()
    
    print("Database seeding process completed.")
