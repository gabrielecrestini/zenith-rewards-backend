# app/database.py

import os
import logging
from contextlib import contextmanager
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
from fastapi import HTTPException

# Configura il logging
logger = logging.getLogger(__name__)

# --- Inizializzazione del Connection Pool ---
db_pool = None

def initialize_db_pool():
    """Inizializza il pool di connessioni a PostgreSQL."""
    global db_pool
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.critical("DATABASE_URL non è impostata! Impossibile connettersi al database.")
        # In un'app reale, potresti voler terminare l'avvio qui
        return

    try:
        db_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,  # Numero minimo di connessioni da tenere aperte
            maxconn=10, # Numero massimo di connessioni da creare
            dsn=database_url,
            cursor_factory=DictCursor # Per ottenere risultati come dizionari
        )
        logger.info("Pool di connessioni al database inizializzato con successo.")
    except psycopg2.OperationalError as e:
        logger.critical(f"Errore critico durante l'inizializzazione del pool di connessioni: {e}", exc_info=True)
        db_pool = None # Assicura che il pool sia None se l'inizializzazione fallisce

@contextmanager
def get_db_connection():
    """
    Fornisce una connessione al database dal pool.
    Usa un context manager per garantire che la connessione venga restituita al pool.
    """
    if not db_pool:
        raise HTTPException(status_code=503, detail="Il servizio database non è disponibile.")
    
    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
    except Exception as e:
        logger.error(f"Errore nell'ottenere una connessione dal pool: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail="Impossibile connettersi al database.")
    finally:
        if conn:
            db_pool.putconn(conn)

def _execute_pg_query(sql_query: str, params: tuple = None, fetch_one: bool = False, fetch_all: bool = False, error_context: str = "operazione database"):
    """
    Esegue una query PostgreSQL usando una connessione dal pool e gestisce le transazioni.
    """
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                logger.debug(f"Executing SQL: {sql_query} with params: {params}")

                if params:
                    cursor.execute(sql_query, params)
                else:
                    cursor.execute(sql_query)
                
                # Le operazioni DML (INSERT, UPDATE, DELETE) richiedono un commit
                if any(keyword in sql_query.upper() for keyword in ["INSERT", "UPDATE", "DELETE", "SELECT"]):
                    conn.commit()

                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
                return None

    except psycopg2.Error as e:
        # Il context manager 'get_db_connection' gestirà il rollback implicito
        logger.error(f"Errore PostgreSQL ({error_context}): Code={e.pgcode}, Message={e.pgerror.strip()}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Errore database ({error_context}): {e.pgerror.strip()}")
    except Exception as e:
        logger.error(f"Errore inaspettato durante l'operazione PostgreSQL ({error_context}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Errore interno del server durante {error_context}.")