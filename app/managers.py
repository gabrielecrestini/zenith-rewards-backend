# app/managers.py

import os
import stripe
import logging
from datetime import datetime, timezone, timedelta
import json
from typing import Literal

from fastapi import HTTPException
from .database import _execute_pg_query # <-- Importa la funzione ottimizzata
from .models import * # Importa tutti i modelli

# Il codice delle classi UserManager, AIManager, ContestManager, ShopManager va qui.
# È identico a quello che hai fornito, ma con due piccole modifiche:
# 1. Non ha più bisogno della funzione _execute_pg_query definita localmente, la importa.
# 2. Non ha più bisogno delle definizioni dei modelli, le importa.

# Esempio di come apparirà l'inizio di una classe
class UserManager:
    def __init__(self): pass

    def sync_user(self, user_data: UserSyncRequest):
        # Il resto del codice della funzione è IDENTICO
        current_utc_time = datetime.now(timezone.utc)
        logger.info(f"Attempting to sync user: {user_data.user_id}")
        
        user_record = _execute_pg_query(
            "SELECT user_id, last_login_at, login_streak, daily_ai_generations_used, last_generation_reset_date, daily_votes_used, last_vote_reset_date FROM users WHERE user_id = %s",
            (user_data.user_id,), fetch_one=True, error_context="user sync fetch"
        )
        # ... e così via per tutte le altre funzioni e classi.
        # ... (incolla qui il resto del codice delle classi Manager dal tuo file originale)