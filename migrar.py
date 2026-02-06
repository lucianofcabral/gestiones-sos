from src.db.database import SQLiteDB


db = SQLiteDB()

db.migrar()
