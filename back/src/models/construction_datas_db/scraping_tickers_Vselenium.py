from bs4 import BeautifulSoup
import requests
import time
import pandas as pd
import numpy as np
import yfinance as yf
import html5lib
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


################################ TOUS LES TICKERS DES INDICES CONVERTIS EN YFINANCE ################################
def all_tickers_yf():
    all_tickers = {}  # Dictionnaire final

    # Scraping avec Requests
    all_tickers.update(scrape_request())  # Ajoute les tickers via requests
    
    # Scraping avec Selenium pour certains indices
    all_tickers.update(scrape_selenium())  # Ajoute les tickers via Selenium

    # Ajouter les tickers du STOXX50
    all_tickers.update(stoxx50_tickers())

    # Normalisation des tickers en format Yahoo Finance
    all_tickers_yf = convert_format_yfinance(all_tickers)

    print(f"[✅] Le fichier scraping a bien été enregistré")
    return all_tickers_yf


################################ SCRAPPING VIA REQUEST ################################
def scrape_request():
    urls = {
        "CAC40": "https://fr.tradingview.com/symbols/EURONEXT-PX1/components/",
        "DAX40": "https://fr.tradingview.com/symbols/XETR-DAX/components/",
        "Italie40": "https://fr.tradingview.com/symbols/INDEX-FTSEMIB/components/",
        "Espagne35": "https://fr.tradingview.com/symbols/BME-IBC/components/",
        "Angleterre100": "https://fr.tradingview.com/symbols/FTSE-UKX/components/",
        "NASDAQ100": "https://fr.tradingview.com/symbols/NASDAQ-NDX/components/",
        "Dow Jones": "https://fr.tradingview.com/symbols/DJ-DJI/components/",
        "Belgique20": "https://fr.tradingview.com/symbols/EURONEXT-BEL20/components/",
        "Paysbas25": "https://fr.tradingview.com/symbols/EURONEXT-AEX/components/",
        "Finlande25": "https://fr.tradingview.com/symbols/OMXHEX-OMXH25/components/",
        "Suède30": "https://fr.tradingview.com/symbols/OMXSTO-OMXS30/components/",
        "Danemark25": "https://fr.tradingview.com/symbols/OMXCOP-OMXC25/components/"
    }

    tickers_request = {}
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"}

    for indice, url in urls.items():
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        tickers = [i.text.strip() for i in soup.select("a.tickerNameBox-GrtoTeat")]
        tickers_request[indice] = tickers

    return tickers_request


################################ SCRAPPING VIA SELENIUM ################################
def scrape_selenium():
    # Initialisation de Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")  # obligatoire sur Render
    options.add_argument("--disable-dev-shm-usage")  # éviter les crashs
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Dictionnaire des indices avec leurs URLs
    urls_selenium = {
        "SP500": "https://fr.tradingview.com/symbols/SPX/components/",
        "Japon225": "https://fr.tradingview.com/symbols/TVC-NI225/components/"
    }
    
    tickers_selenium = {}  # Dictionnaire pour stocker les tickers
    
    for indice, url in urls_selenium.items():
        driver.get(url)
        wait = WebDriverWait(driver, 10)

        # Cliquer sur "Charger plus" jusqu'à ce que le bouton disparaisse
        while True:
            try:
                button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".loadMoreWrapper-YZEOoLh1 button")))
                button.click()
            except:
                break  # Sortie de boucle quand il n'y a plus de bouton

        # Récupération des tickers et stockage dans le dictionnaire
        tickers = [i.text for i in driver.find_elements(By.CSS_SELECTOR, "a.tickerNameBox-GrtoTeat")]
        tickers_selenium[indice] = tickers

    driver.quit()  # Fermeture du navigateur

    return tickers_selenium


################################ SCRAPPING TICKERS STOXX50 ################################
def stoxx50_tickers():
    ticker_stoxx50 = {"STOXX50":
        ['MC.PA', 'SAP.DE', 'RMS.PA', 'ASML.AS', 'OR.PA', 'ITX.MC', 'SIE.DE', 
        'DTE.DE', 'SU.PA', 'AIR.PA', 'SAN.PA', 'TTE.PA', 'ALV.DE', 'EL.PA', 
        'SAF.PA', 'AI.PA', 'ABI.BR', 'PRX.AS', 'IBE.MC', 'CS.PA', 'SAN.MC', 
        'ISP.MI', 'RACE.MI', 'BNP.PA', 'MUV2.DE', 'UCG.MI', 'ENEL.MI', 
        'BBVA.MC', 'DG.PA', 'MBG.DE', 'INGA.AS', 'VOW3.DE', 'BMW.DE', 
        'ADYEN.AS', 'ADS.DE', 'SGO.PA', 'DB1.DE', 'BN.PA', 'IFX.DE', 'BAS.DE', 
        'ENI.MI', 'WKL.AS', 'DHL.DE', 'NDA-SE.ST', 'STLAP.PA', 'AD.AS', 'KER.PA', 
        'RI.PA', 'NOKIA.HE', 'BAYN.DE']
    }
    return ticker_stoxx50


################################ CONVERTION TICKERS EN TICKERS YFINANCE ################################
def convert_format_yfinance(tickers_dict):
    
    suffixes = {
        "CAC40": ".PA",
        "DAX40": ".DE",
        "Italie40": ".MI",
        "Espagne35": ".MC",
        "Angleterre100": ".L",
        "NASDAQ100": "",  # Pas de suffixe pour le NASDAQ
        "Dow Jones": "",  # Pas de suffixe pour le Dow Jones
        "Belgique20": ".BR",
        "Paysbas25": ".AS",
        "Finlande25": ".HE",
        "Suède30": ".ST",
        "Danemark25": ".CO",
        "SP500": "",  # Pas de suffixe pour S&P500
        "Japon225": ".T" 
    }

    tickers_yf = {}  # Nouveau dictionnaire pour stocker les tickers normalisés

    for indice, tickers in tickers_dict.items():
        # Ne rien modifier pour STOXX50 (déjà au bon format)
        if indice == "STOXX50":
            tickers_yf[indice] = tickers
            continue
        # Nettoyage des tickers : suppression des points à la fin et remplacement des autres points par des tirets
        cleaned_tickers = []
        for ticker in tickers:
            ticker = ticker.rstrip('.')  # Supprimer les points à la fin
            ticker = ticker.replace('.', '-')  # Remplacer les points restants par des tirets
            ticker = ticker.replace('_', '-')  # Remplacer les underscores restants par des tirets
            cleaned_tickers.append(ticker)
            
        # Ajouter le suffixe pour chaque ticker
        tickers_yf[indice] = [ticker + suffixes.get(indice, "") for ticker in cleaned_tickers]

    # Cas particulier pour le CAC40 : ajouter MT.AS
    tickers_yf["CAC40"].append("MT.AS")

    return tickers_yf

################################ LANCEMENT ################################
if __name__ == "__main__":
    tickers_yf = all_tickers_yf()
    print(tickers_yf)