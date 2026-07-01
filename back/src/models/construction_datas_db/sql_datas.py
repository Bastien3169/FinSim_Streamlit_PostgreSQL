"""
Gestion des tables de données financières avec SQLAlchemy Core
- Création des tables (indices, stocks, cryptos, ETFs + historiques)
- Import des CSV vers PostgreSQL
"""
import os
import glob
import pandas as pd
from sqlalchemy import text
from src.api_conn.database_conn import engine

# =====================================================
# CRÉATION DES TABLES (SQLAlchemy Core)
# =====================================================
def creation_db():
    """Crée toutes les tables de données financières"""
    
    with engine.begin() as conn:
        # Pour accepter le format DD-MM-YYYY
        conn.execute(text("SET datestyle = ymd;"))

        # DROP TABLES dans l'ordre inverse des dépendances
        conn.execute(text("DROP TABLE IF EXISTS historique_etfs CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS historique_cryptos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS historique_stocks CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS historique_indices CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS stocks_indices CASCADE;"))  
        conn.execute(text("DROP TABLE IF EXISTS etfs_infos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS cryptos_infos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS stocks_infos CASCADE;"))
        conn.execute(text("DROP TABLE IF EXISTS indices_infos CASCADE;"))

        # ----------- Tables INFOS ----------- #
        
        # Indices (DOIT être créé avant stocks à cause de la FK)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS indices_infos (
                short_name_indice TEXT,
                ticker_indice_yf TEXT PRIMARY KEY,
                nom_indice TEXT,
                devise TEXT,
                place_boursiere_indice TEXT,
                nombres_entreprises INTEGER
            )
        """))

        # Stocks (🔄 MODIFIÉ : sans Ticker_Indice_Yf et Ponderation)
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks_infos (
                ticker_stocks_yf TEXT PRIMARY KEY,
                short_name_stocks TEXT,
                ticker_stocks TEXT,
                secteur_activite TEXT,
                pays_stocks TEXT,
                place_boursiere TEXT,
                capitalisation_boursiere NUMERIC(18,2)
            )
        """))
        
        # 🆕 NOUVELLE TABLE : liaison many-to-many
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS stocks_indices (
                id SERIAL PRIMARY KEY,
                ticker_stocks_yf TEXT NOT NULL,
                ticker_indice_yf TEXT NOT NULL,
                ponderation NUMERIC(10,4),
                FOREIGN KEY (ticker_stocks_yf) REFERENCES stocks_infos(ticker_stocks_yf) ON DELETE CASCADE,
                FOREIGN KEY (ticker_indice_yf) REFERENCES indices_infos(ticker_indice_yf) ON DELETE CASCADE,
                UNIQUE (ticker_stocks_yf, ticker_indice_yf)
            )
        """))

        # Cryptos
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS cryptos_infos (
                short_name_cryptos TEXT,
                ticker_cryptos_yf TEXT PRIMARY KEY,
                ticker_cryptos TEXT,
                prix_actuel NUMERIC(18,6),
                capitalisation_boursiere NUMERIC(18,2),
                offre_en_circulation_non_arrondie NUMERIC(18,2),
                offre_en_circulation NUMERIC(18,2),
                ath NUMERIC(18,6),
                maj DATE
            )
        """))
        
        # ETFs
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS etfs_infos (
                short_name_etf TEXT,
                ticker_etf_yf TEXT PRIMARY KEY,
                ticker_etf TEXT,
                devise TEXT,
                place_boursiere_etf TEXT,
                volume_moyen NUMERIC(18,2),
                frais_pct NUMERIC(6,4)
            )
        """))
        
        # ----------- Tables HISTORIQUES ----------- #
        
        # Historique indices
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historique_indices (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                close NUMERIC(18,6),
                ticker_indice_yf TEXT,
                short_name_indice TEXT,
                UNIQUE (date, ticker_indice_yf)
            )
        """))

        # Historique actions
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historique_stocks (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                close NUMERIC(30,6),
                ticker_stocks_yf TEXT,
                short_name_stocks TEXT,
                UNIQUE (date, ticker_stocks_yf)
            )
        """))

        # Historique cryptos
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historique_cryptos (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                close NUMERIC(18,6),
                ticker_cryptos_yf TEXT,
                short_name_cryptos TEXT,
                UNIQUE (date, short_name_cryptos)
            )
        """))

        # Historique ETF
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS historique_etfs (
                id SERIAL PRIMARY KEY,
                date DATE NOT NULL,
                close NUMERIC(18,6),
                ticker_etf_yf TEXT,
                short_name_etf TEXT,
                UNIQUE (date, ticker_etf_yf)
            )
        """))

        # ----------- Index utiles ----------- #
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hist_indices_name_date 
            ON historique_indices(short_name_indice, date)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hist_stocks_name_date 
            ON historique_stocks(short_name_stocks, date)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hist_cryptos_name_date 
            ON historique_cryptos(short_name_cryptos, date)
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_hist_etfs_name_date 
            ON historique_etfs(short_name_etf, date)
        """))
    
    print("[✅] Tables PostgreSQL créées avec succès.")

# =====================================================
# IMPORT CSV AVEC PANDAS + SQLAlchemy
# =====================================================
IMPORT_ORDER = [
    "indices_infos.csv",
    "stocks_infos.csv",
    "etfs_infos.csv",
    "cryptos_infos.csv",
    "historique_indices.csv",
    "historique_stocks.csv",
    "historique_etfs.csv",
    "historique_cryptos.csv",
]

def import_csv_compo_indices(csv_bdd):
    print(f"[📁] Import CSV dans l'ordre contrôlé")

    for filename in IMPORT_ORDER:
        path = os.path.join(csv_bdd, filename)

        if not os.path.exists(path):
            print(f"[⚠️] Fichier manquant : {filename}")
            continue

        try:
            df = pd.read_csv(path)

            if "date" in df.columns:
                df["date"] = pd.to_datetime(df["date"], utc=True).dt.date

            table_name = filename.replace(".csv", "")

            # 🆕 AJOUT : Traitement spécial pour stocks_infos.csv
            if filename == "stocks_infos.csv":
                # 1. Extraire les stocks uniques (sans ticker_indice_yf et ponderation)
                stocks_unique = df[[
                    'ticker_stocks_yf', 'short_name_stocks', 'ticker_stocks',
                    'secteur_activite', 'pays_stocks', 'place_boursiere', 
                    'capitalisation_boursiere'
                ]].drop_duplicates(subset=['ticker_stocks_yf'])
            
                
                # Import des stocks uniques
                stocks_unique.to_sql("stocks_infos", engine, if_exists="append", index=False, method="multi")
                print(f"[✅] Table 'stocks_infos' importée ({len(stocks_unique)} entreprises uniques)")
                
                # 2. Extraire les relations pour la table de liaison
                liaison = df[['ticker_stocks_yf', 'ticker_indice_yf', 'ponderation']].copy()
                liaison.columns = ['ticker_stocks_yf', 'ticker_indice_yf', 'ponderation']
                
                # Import des relations
                liaison.to_sql("stocks_indices", engine, if_exists="append", index=False, method="multi")
                print(f"[✅] Table 'stocks_indices' remplie ({len(liaison)} relations)")
            else:
                # Import normal pour les autres fichiers
                df.to_sql(table_name, engine, if_exists="append", index=False, method="multi")
                print(f"[✅] Table '{table_name}' importée ({len(df)} lignes)")

        except Exception as e:
            print(f"[❌] Erreur import {filename} : {e}")

    print("[✅] Importation CSV terminée.")


# =====================================================
# FONCTION PRINCIPALE
# =====================================================
def main_creation_db(csv_bdd):
    """
    Initialise la base de données complète :
    1. Crée les tables
    2. Importe les CSV
    """
    print("🔧 Initialisation de la base de données...")
    print(f"📂 Dossier CSV : {csv_bdd}")
    
    # Étape 1 : Créer les tables
    creation_db()
    
    # Étape 2 : Importer les CSV
    import_csv_compo_indices(csv_bdd)
    
    print("✅ Base de données initialisée avec succès !")