from app.db.session import SessionLocal, init_db
from app.services.seed import run_seed

if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        print(run_seed(session))
