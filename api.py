from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import auth
from src.models.construction_datas_db.sql_datas import main_creation_db

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    auth.clean_expired_sessions()

    print("🔄 Chargement des données CSV dans la base de données...")
    csv_path = Path(__file__).parent / "csv" / "csv_bdd"
    main_creation_db(str(csv_path))
    print("✅ Données CSV chargées avec succès.")
