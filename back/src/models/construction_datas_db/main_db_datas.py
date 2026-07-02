# main.py
import os
from src.models.construction_datas_db import scraping_tickers
from src.models.construction_datas_db import composition_indices
from src.models.construction_datas_db import infos_indices
from src.models.construction_datas_db import infos_stocks
from src.models.construction_datas_db import infos_cryptos
from src.models.construction_datas_db import infos_etfs
from src.models.construction_datas_db import hist_indices
from src.models.construction_datas_db import hist_stocks
from src.models.construction_datas_db import hist_cryptos
from src.models.construction_datas_db import hist_etfs
from src.models.construction_datas_db import sql_datas
'''
from . import scraping_tickers  # Pour récupérer les tickers
from . import composition_indices  # Pour obtenir les infos des entreprises par indice
from . import infos_stocks  # Pour concaténer les informations des entreprises et les stocker en CSV
from . import infos_indices  # Pour récupérer les infos des indices et les stocker en CSV
from . import hist_indices  # Pour récupérer l'historique des prix des indices
from . import infos_cryptos  # Pour récupérer les infos des cryptomonnaies
from . import hist_cryptos  # Pour récupérer l'historique des prix des cryptomonnaies
from . import hist_stocks  # Pour récupérer l'historique des prix des entreprises
from . import sql_datas # Pour créer la base de donnée sql
'''

def main_db_datas(dossier_csv = "csv", csv_bdd = "csv/csv_bdd"):

    '''# Étape 1: Récupérer et sauvegarder les tickers de chaque indice et stocks au format yfinance
    scraping_tickers.all_tickers_yf()
    print("[1/12 ✅] Les tickers des indices et des stocks ont été récupérés et sauvegardés.")

    # Étape 2: Scraper les tickers de chaque indice et Récupérer les informations des entreprises pour chaque indice
    composition_indices.csv_indices(dossier_csv)
    print("[2/12 ✅] Les tickers des indices et les informations des entreprises ont été récupérés et sauvegardés.")
    
    # Étape 3: Concaténer et sauvegarder les données des entreprises
    infos_stocks.infos_stocks(dossier_csv, csv_bdd) 
    print("[3/12 ✅] Les informations des entreprises ont été concaténées et sauvegardées.")

    # Étape 4: Récupérer et sauvegarder les informations des indices
    infos_indices.infos_indices(dossier_csv, csv_bdd)
    print("[4/12 ✅] Les informations des indices ont été récupérées et sauvegardées.")
    
    # Étape 5: Récupérer et sauvegarder les informations des cryptomonnaies
    infos_cryptos.infos_cryptos(dossier_csv, csv_bdd)
    print("[5/12 ✅] Les informations des cryptomonnaies ont été récupérées et sauvegardées.")

    # Étape 6: Récupérer et sauvegarder les informations des cryptomonnaies
    print("[6/12 ✅] Les informations des cryptomonnaies ont été récupérées et sauvegardées.")

    # Étape 7: Récupérer et sauvegarder les informations des etfs
    infos_etfs.infos_etfs(csv_bdd)
    print("[7/12 ✅] Les informations des etfs ont été récupérées et sauvegardées.")
    
    # Étape 8: Récupérer et sauvegarder l'historique des prix des indices
    hist_indices.recuperer_et_clean_indices(csv_bdd)
    print("[8/12 ✅] L'historique des indices a été récupéré et sauvegardé.")

    # Étape 9: Récupérer et sauvegarder l'historique des prix des entreprises
    hist_stocks.recuperer_et_clean_stocks(csv_bdd)
    print("[9/12 ✅] L'historique des entreprises a été récupéré et sauvegardé.")
    
    # Étape 10: Récupérer et sauvegarder l'historique des prix des cryptomonnaies
    hist_cryptos.hist_cryptos(csv_bdd)
    print("[10/12 ✅] L'historique des cryptomonnaies a été récupéré et sauvegardé.")
    
    # Étape 11: Récupérer et sauvegarder l'historique des prix des etfs
    hist_etfs.hist_etfs(csv_bdd)
    print("[11/12 ✅] L'historique des etfs a été récupéré et sauvegardé.")'''
    
    # Étape 12 : Création de la base de donnée
    sql_datas.main_creation_db(csv_bdd)
    print("[12/12 ✅] La base de données a été créée et les données ont été importées.")

if __name__ == "__main__":
    main_db_datas("csv", "csv/csv_bdd")

