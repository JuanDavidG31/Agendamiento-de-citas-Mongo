import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def get_postgres_connection():
    try:
        conn = psycopg2.connect(os.getenv("NEON_DATABASE_URL"))
        return conn
    except Exception as e:
        print(f"Error conectando a PostgreSQL (Neon): {e}")
        return None

def get_mongo_db():
    try:
        client = MongoClient(os.getenv("MONGO_DATABASE_URL"))
        db = client["hospital_db"] # Nombre de tu base de datos en MongoDB
        return db
    except Exception as e:
        print(f"Error conectando a MongoDB: {e}")
        return None