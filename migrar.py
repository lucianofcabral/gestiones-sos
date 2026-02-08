from src.db.connection import get_database


db = get_database()

db.migrar()
