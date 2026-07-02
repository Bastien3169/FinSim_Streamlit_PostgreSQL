import math
import os
import jwt
import bcrypt
import psycopg2
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.models.datas_db.datas_queries import (
    FinanceDatabaseStocks,
    FinanceDatabaseIndice,
    FinanceDatabaseCryptos,
    FinanceDatabaseEtfs,
    calculate_rendement
)
from src.api_conn.database_conn import get_connection

app = FastAPI()
security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stocks = FinanceDatabaseStocks()
indices = FinanceDatabaseIndice()
cryptos = FinanceDatabaseCryptos()
etfs = FinanceDatabaseEtfs()

def serialize_df(df):
    records = df.to_dict(orient="records")
    return [{k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()} for row in records]

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expiré")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token invalide")

# ============================================
# ROUTES AUTH
# ============================================
@app.post("/api/auth/register")
def register(data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email et mot de passe requis")
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed))
            conn.commit()
    except psycopg2.errors.UniqueViolation:
        raise HTTPException(status_code=400, detail="Email déjà utilisé")
    return {"message": "Compte créé"}

@app.post("/api/auth/login")
def login(data: dict):
    email = data.get("email")
    password = data.get("password")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
    if not row or not bcrypt.checkpw(password.encode(), row[0].encode()):
        raise HTTPException(status_code=401, detail="Identifiants invalides")
    token = create_access_token({"sub": email})
    return {"access_token": token}

# ============================================
# ROUTES DATA - STOCKS
# ============================================
@app.get("/api/stocks/list")
def get_stocks_list():
    return {"stocks": stocks.get_list_stocks()}

@app.get("/api/stocks/infos")
def get_stocks_infos(name: str):
    df = stocks.get_infos_stocks(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Stock non trouvé")
    return serialize_df(df)

@app.get("/api/stocks/prix")
def get_stocks_prix(name: str):
    df = stocks.get_prix_date(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Prix non trouvés")
    return serialize_df(df)

# ============================================
# ROUTES DATA - INDICES
# ============================================
@app.get("/api/indices/list")
def get_indices_list():
    return {"indices": indices.get_list_indices()}

@app.get("/api/indices/infos")
def get_indices_infos(name: str):
    df = indices.get_infos_indices(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Indice non trouvé")
    return serialize_df(df)

@app.get("/api/indices/prix")
def get_indices_prix(name: str):
    df = indices.get_prix_date(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Prix non trouvés")
    return serialize_df(df)

@app.get("/api/indices/composition")
def get_indices_composition(name: str):
    df = indices.get_composition_indice(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Composition non trouvée")
    return serialize_df(df)

# ============================================
# ROUTES DATA - CRYPTOS
# ============================================
@app.get("/api/cryptos/list")
def get_cryptos_list():
    return {"cryptos": cryptos.get_list_cryptos()}

@app.get("/api/cryptos/infos")
def get_cryptos_infos(name: str):
    df = cryptos.get_infos_cryptos(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Crypto non trouvée")
    return serialize_df(df)

@app.get("/api/cryptos/prix")
def get_cryptos_prix(name: str):
    df = cryptos.get_prix_date(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Prix non trouvés")
    return serialize_df(df)

# ============================================
# ROUTES DATA - ETFS
# ============================================
@app.get("/api/etfs/list")
def get_etfs_list():
    return {"etfs": etfs.get_list_etfs()}

@app.get("/api/etfs/infos")
def get_etfs_infos(name: str):
    df = etfs.get_infos_etfs(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="ETF non trouvé")
    return serialize_df(df)

@app.get("/api/etfs/prix")
def get_etfs_prix(name: str):
    df = etfs.get_prix_date(name)
    if df.empty:
        raise HTTPException(status_code=404, detail="Prix non trouvés")
    return serialize_df(df)

# ============================================
# ROUTES DATA - RENDEMENTS
# ============================================
@app.get("/api/rendement")
def get_rendement(name: str, type: str, periods: str):
    periods_list = [int(p) for p in periods.split(",")]
    if type == "indice":
        df = indices.get_prix_date(name)
    elif type == "stock":
        df = stocks.get_prix_date(name)
    elif type == "crypto":
        df = cryptos.get_prix_date(name)
    elif type == "etf":
        df = etfs.get_prix_date(name)
    else:
        raise HTTPException(status_code=400, detail="Type invalide")
    if df.empty:
        raise HTTPException(status_code=404, detail="Données non trouvées")
    return calculate_rendement(df, periods_list)