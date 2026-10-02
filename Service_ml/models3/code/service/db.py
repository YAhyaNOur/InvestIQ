from sqlalchemy import create_engine

DB_URL = "postgresql://postgres:admin@localhost:5432/smartstart_db"

engine = create_engine(DB_URL)

def get_engine():
    return engine