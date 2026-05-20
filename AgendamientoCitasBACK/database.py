import os
import psycopg2
from pymongo import MongoClient
from dotenv import load_dotenv



# Cargar las variables de entorno desde el archivo .env
load_dotenv()

def get_postgres_connection():
    """
    Establece y retorna la conexión activa hacia el clúster de Neon (PostgreSQL).
    Aplica los principios de aislamiento y atomicidad (ACID).
    """
    try:
        # Lee la URI directa del entorno
        db_url = os.getenv("NEON_DATABASE_URL")
        
        # Realiza la conexión remota utilizando el driver psycopg2
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"❌ Error crítico al conectar con PostgreSQL en Neon: {e}")
        return None

def get_mongo_db():
    """
    Establece y retorna el acceso a la base de datos documental de MongoDB.
    """
    try:
        client = MongoClient(os.getenv("MONGO_DATABASE_URL"))
        db = client["hospital_db"]
        return db
    except Exception as e:
        print(f"❌ Error crítico al conectar con MongoDB: {e}")
        return None