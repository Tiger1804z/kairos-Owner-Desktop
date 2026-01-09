"""
KAIROS Owner Desktop - Gestion de la connexion à la base de données
"""
import os
import psycopg2
from psycopg2.extensions import connection
from dotenv import load_dotenv


load_dotenv()


def get_connection() -> connection:
    """
    Établit et retourne une connexion à la base de données PostgreSQL.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set in the environment variables.")

    return psycopg2.connect(database_url, sslmode='require')

def test_connection():
    """
    Teste la connexion à la base de données.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur :
            cur.execute("SELECT 1;")
            result = cur.fetchone()
            print("✅ Database connection successful:", result)
    except Exception as e:
        print("❌ Database connection failed:")
        print(e)
    finally:
        if 'conn' in locals():
            conn.close()
            
if __name__ == "__main__":
    test_connection()