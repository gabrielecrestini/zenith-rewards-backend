# app/main.py
import os
import logging
import stripe
import vertexai
from contextlib import asynccontextmanager 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import initialize_db_pool, close_db_pool
from .routers import users, ai, payments, general

# --- Configurazione Iniziale ---
load_dotenv()

# Configura il logging di base
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Inizializzazione Servizi ---
app = FastAPI(
    title="Zenith Rewards Backend",
    description="Backend per la gestione di utenti, AI, pagamenti e gamification per Zenith Rewards.",
    lifespan=lifespan # Usa il nuovo gestore del ciclo di vita
)

# Carica le configurazioni dalle variabili d'ambiente
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY")
GCP_PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
# ... (carica tutte le altre variabili d'ambiente come prima)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Codice da eseguire all'avvio dell'applicazione
    logger.info("Avvio dell'applicazione Zenith Rewards...")
    initialize_db_pool()
    initialize_vertex_ai()
    initialize_stripe()
    yield
    # Codice da eseguire allo spegnimento dell'applicazione
    logger.info("Spegnimento dell'applicazione Zenith Rewards...")
    close_db_pool()

def initialize_vertex_ai():
    global gemini_flash_model, gemini_pro_vision_model, vertexai_initialized
    GCP_SA_KEY_JSON_STR = os.environ.get("GCP_SA_KEY_JSON")
    if all([GCP_PROJECT_ID, GCP_REGION, GCP_SA_KEY_JSON_STR]):
        try:
            # ... (il tuo codice di inizializzazione di Vertex AI va qui) ...
            vertexai.init(project=GCP_PROJECT_ID, location=GCP_REGION)
            # ...
            logger.info("Vertex AI inizializzato con successo.")
        except Exception as e:
            logger.error(f"Errore di configurazione Vertex AI: {e}", exc_info=True)
    else:
        logger.warning("Credenziali GCP mancanti. Vertex AI è disabilitato.")

def initialize_stripe():
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
        logger.info("Chiave API Stripe caricata.")
    else:
        logger.warning("STRIPE_SECRET_KEY non configurata. Le funzionalità Stripe sono disabilitate.")

# --- Middleware (CORS) ---
FRONTEND_URL = os.environ.get("NEXT_PUBLIC_FRONTEND_URL", "https://cashhh-52f38.web.app")
allowed_origins = [
    "http://localhost:3000",
    "https://cashhh-52f38.web.app",
    "https://cashhh-52738.web.app",
    FRONTEND_URL
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Includi i Router ---
app.include_router(users.router)
app.include_router(ai.router)
app.include_router(payments.router)
app.include_router(general.router)

# --- Endpoint Radice ---
@app.get("/")
def read_root():
    return {"message": "Zenith Rewards Backend è operativo. Accedi alla documentazione API su /docs."}

# Commento per forzare un nuovo deployment