import re
import certifi
import pandas as pd
import requests
from io import StringIO

headers = {"User-Agent": "Mozilla/5.0"}

WIKI_SOURCES = {
    "CAC40":         ("https://fr.wikipedia.org/wiki/CAC_40", 2, "Mnémo"),
    "DAX40":         ("https://en.wikipedia.org/wiki/DAX", 4, "Ticker"),
    "Italie40":      ("https://en.wikipedia.org/wiki/FTSE_MIB", 1, "Ticker"),
    "Espagne35":     ("https://en.wikipedia.org/wiki/IBEX_35", 2, "Ticker"),
    "Angleterre100": ("https://en.wikipedia.org/wiki/FTSE_100_Index", 6, "Ticker"),
    "NASDAQ100":     ("https://en.wikipedia.org/wiki/Nasdaq-100", 5, "Ticker"),
    "Dow Jones":      ("https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average", 1, "Symbol"),
    "Belgique20":    ("https://en.wikipedia.org/wiki/BEL20", 2, "Ticker symbol"),
    "Paysbas25":     ("https://en.wikipedia.org/wiki/AEX_index", 3, "Ticker"),
    "Finlande25":    ("https://en.wikipedia.org/wiki/OMX_Helsinki_25", 1, "Ticker"),
    "Suède30":       ("https://en.wikipedia.org/wiki/OMX_Stockholm_30", 1, "Ticker"),
    "Danemark25":    ("https://en.wikipedia.org/wiki/OMX_Copenhagen_25", 0, "Ticker symbol"),
    "SP500":         ("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", 0, "Symbol"),
}

def clean_ticker(ticker, indice):
    ticker = str(ticker).strip()
    if indice == "CAC40":
        return f"{ticker}.PA"
    if indice == "Angleterre100": # Remplace les points internes au ticker (pas le suffixe) par des tirets
        parts = ticker.split(".")
        ticker = "-".join(parts)  # BT.A → BT-A, ticker normal → ticker
        return f"{ticker}.L"
    if indice == "Belgique20":
        ticker = re.sub(r"Euronext \w+:\s*", "", ticker).strip()
        return f"{ticker}.BR"
    if indice == "Danemark25":
        ticker = ticker.replace(" ", "-")
        return f"{ticker}.CO"
    return ticker

def get_tickers(url, table_idx, col, indice):
    try:
        response = requests.get(url, verify=certifi.where(), headers=headers)
        df = pd.read_html(StringIO(response.text))[table_idx]
        if col not in df.columns:
            print(f"  ⚠️ {indice} — Colonne '{col}' introuvable : {list(df.columns)}")
            return []
        tickers = df[col].dropna().tolist()
        tickers = [clean_ticker(t, indice) for t in tickers]
        tickers = [t for t in tickers if len(t) <= 15]
        if indice == "NASDAQ100":
            tickers = [t for t in tickers if t != "GOOG"]
        return tickers
    except Exception as e:
        print(f"  ❌ {indice} : {e}")
        return []

def stoxx50_tickers():
    return {"STOXX50": [
        'MC.PA', 'SAP.DE', 'RMS.PA', 'ASML.AS', 'OR.PA', 'ITX.MC', 'SIE.DE',
        'DTE.DE', 'SU.PA', 'AIR.PA', 'SAN.PA', 'TTE.PA', 'ALV.DE', 'EL.PA',
        'SAF.PA', 'AI.PA', 'ABI.BR', 'PRX.AS', 'IBE.MC', 'CS.PA', 'SAN.MC',
        'ISP.MI', 'RACE.MI', 'BNP.PA', 'MUV2.DE', 'UCG.MI', 'ENEL.MI',
        'BBVA.MC', 'DG.PA', 'MBG.DE', 'INGA.AS', 'VOW3.DE', 'BMW.DE',
        'ADYEN.AS', 'ADS.DE', 'SGO.PA', 'DB1.DE', 'BN.PA', 'IFX.DE', 'BAS.DE',
        'ENI.MI', 'WKL.AS', 'DHL.DE', 'NDA-SE.ST', 'STLAP.PA', 'AD.AS', 'KER.PA',
        'RI.PA', 'NOKIA.HE', 'BAYN.DE'
    ]}

def all_tickers_yf():
    all_tickers = {}

    for indice, (url, table_idx, col) in WIKI_SOURCES.items():
        tickers = get_tickers(url, table_idx, col, indice)
        all_tickers[indice] = tickers
        print(f"  {indice} : {len(tickers)} tickers")

    all_tickers.update(stoxx50_tickers())
    all_tickers["CAC40"].append("MT.AS")

    print(f"[✅] Le fichier scraping a bien été enregistré")
    return all_tickers

if __name__ == "__main__":
    result = all_tickers_yf()
    print(result)