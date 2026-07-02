"""
Page de comparaison de TOUS les actifs (indices, stocks, cryptos, ETFs)
"""
import streamlit as st
from src.api_client.api_client import *
from src.components.components_views import *

def actifs_page(go_to):
    
    # ================= CSS =================
    load_css()
    
    # ================= CONNEXIONS DB =================
    
    # Indices
    datas_indices = FinanceDatabaseIndice()
    liste_indices = datas_indices.get_list_indices()
    indice_default = "S&P 500"
    
    # Stocks
    datas_stocks = FinanceDatabaseStocks()
    liste_stocks = datas_stocks.get_list_stocks()
    stock_default = "Apple Inc."
    
    # Cryptos
    datas_cryptos = FinanceDatabaseCryptos()
    liste_cryptos = datas_cryptos.get_list_cryptos()
    crypto_default = "Bitcoin"
    
    # ⭐ AJOUT : ETFs
    datas_etfs = FinanceDatabaseEtfs()
    liste_etfs = datas_etfs.get_list_etfs()
    etf_default = "Amundi Gold Miners UCITS ETF Di"
    
    # ================= TITRE =================
    display_page_title("⚖️ COMPARAISON DES ACTIFS")
    
    # ================= RENDEMENTS MULTI-ACTIFS =================
    display_multi_actifs_rendement_section(
        datas_indices=datas_indices,
        datas_stocks=datas_stocks,
        datas_cryptos=datas_cryptos,
        datas_etfs=datas_etfs,  # ⭐ AJOUT
        liste_indices=liste_indices,
        liste_stocks=liste_stocks,
        liste_cryptos=liste_cryptos,
        liste_etfs=liste_etfs,  # ⭐ AJOUT
        indice_default=indice_default,
        stock_default=stock_default,
        crypto_default=crypto_default,
        etf_default=etf_default,  # ⭐ AJOUT
        calculate_rendement_func=calculate_rendement,
        style_rendement_func=style_rendement,
        default_periods=[6, 12, 24, 60, 120, 180]
    )
    
    # ================= BOUTON RETOUR =================
    bout_accueil(back_callback=go_to)
    
    # ================= FOOTER =================
    footer()