from src.api_conn.database_conn import get_connection
import pandas as pd

# Fonction utilitaire partagée
def clean_df(df):
    return df.astype(object).where(df.notna(), None)


class FinanceDatabaseStocks:
    def __init__(self):
        pass

    def get_list_stocks(self):
        with get_connection() as conn:
            df = pd.read_sql("SELECT DISTINCT short_name_stocks FROM stocks_infos", conn)
        return df["short_name_stocks"].tolist()

    def get_infos_stocks(self, short_name=None):
        with get_connection() as conn:
            query = "SELECT * FROM stocks_infos"
            if short_name:
                query += " WHERE short_name_stocks = %s"
                df = pd.read_sql(query, conn, params=(short_name,))
            else:
                df = pd.read_sql(query, conn)
        return clean_df(df)

    def get_prix_date(self, actif):
        with get_connection() as conn:
            query = "SELECT date, close FROM historique_stocks WHERE short_name_stocks = %s ORDER BY date"
            df = pd.read_sql(query, conn, params=(actif,))
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
            df = df.sort_values("date").reset_index(drop=True)
        return clean_df(df)


class FinanceDatabaseIndice:
    def __init__(self):
        pass

    def get_list_indices(self):
        with get_connection() as conn:
            df = pd.read_sql("SELECT DISTINCT short_name_indice FROM indices_infos", conn)
        return df["short_name_indice"].tolist()

    def get_infos_indices(self, selected_indice):
        with get_connection() as conn:
            df = pd.read_sql("SELECT * FROM indices_infos WHERE short_name_indice = %s", conn, params=(selected_indice,))
        return clean_df(df)

    def get_prix_date(self, selected_indice):
        with get_connection() as conn:
            query = "SELECT date, close FROM historique_indices WHERE short_name_indice = %s ORDER BY date"
            df = pd.read_sql(query, conn, params=(selected_indice,))
        return clean_df(df)

    def get_composition_indice(self, selected_indice):
        try:
            with get_connection() as conn:
                query = """
                SELECT s.*, si.ponderation
                FROM stocks_infos s
                JOIN stocks_indices si ON s.ticker_stocks_yf = si.ticker_stocks_yf
                JOIN indices_infos i ON si.ticker_indice_yf = i.ticker_indice_yf
                WHERE i.short_name_indice = %s
                ORDER BY s.short_name_stocks
                """
                df = pd.read_sql(query, conn, params=(selected_indice,))

            df_clean = clean_df(df)

            # DEBUG TEMPORAIRE — vérifier le TYPE réel des valeurs manquantes
            mask_cap = df_clean['capitalisation_boursiere'].isna()
            mask_pond = df_clean['ponderation'].isna()

            print(f"🔍 [{selected_indice}] Valeurs cap manquantes:")
            print(df_clean.loc[mask_cap, 'capitalisation_boursiere'].apply(lambda x: (x, type(x))).tolist())

            print(f"🔍 [{selected_indice}] Valeurs pond manquantes:")
            print(df_clean.loc[mask_pond, 'ponderation'].apply(lambda x: (x, type(x))).tolist())

            return df_clean
        except Exception as e:
            print(f"Erreur: {e}")
            return pd.DataFrame()
class FinanceDatabaseCryptos:
    def __init__(self):
        pass

    def get_list_cryptos(self):
        with get_connection() as conn:
            df = pd.read_sql("SELECT DISTINCT short_name_cryptos FROM cryptos_infos", conn)
        return df["short_name_cryptos"].tolist()

    def get_infos_cryptos(self, short_name):
        with get_connection() as conn:
            query = "SELECT * FROM cryptos_infos"
            if short_name:
                query += " WHERE short_name_cryptos = %s"
                df = pd.read_sql(query, conn, params=(short_name,))
            else:
                df = pd.read_sql(query, conn)
        df = df.drop_duplicates(subset=["short_name_cryptos"])
        return clean_df(df)

    def get_prix_date(self, actif):
        with get_connection() as conn:
            query = "SELECT date, close FROM historique_cryptos WHERE short_name_cryptos = %s ORDER BY date"
            df = pd.read_sql(query, conn, params=(actif,))
        return clean_df(df)


class FinanceDatabaseEtfs:
    def __init__(self):
        pass

    def get_list_etfs(self):
        with get_connection() as conn:
            df = pd.read_sql("SELECT short_name_etf FROM etfs_infos", conn)
        return df["short_name_etf"].tolist()

    def get_infos_etfs(self, short_name=None):
        with get_connection() as conn:
            query = "SELECT * FROM etfs_infos"
            if short_name:
                query += " WHERE short_name_etf = %s"
                df = pd.read_sql(query, conn, params=(short_name,))
            else:
                df = pd.read_sql(query, conn)
        return clean_df(df)

    def get_prix_date(self, actif):
        with get_connection() as conn:
            query = "SELECT date, close FROM historique_etfs WHERE short_name_etf = %s ORDER BY date"
            df = pd.read_sql(query, conn, params=(actif,))
        return clean_df(df)


def calculate_rendement(df, periods):
    rendement = {}
    for period_months in periods:
        start_date = df["date"].max() - pd.DateOffset(months=period_months)
        df_period = df[df["date"] >= start_date]
        if len(df_period) > 1:
            start_close = df_period.iloc[0]["close"]
            end_close = df_period.iloc[-1]["close"]
            rendement[f"{period_months} mois"] = "{:.2f}".format((end_close - start_close) / start_close * 100)
        else:
            rendement[f"{period_months} mois"] = None
    return rendement


def style_rendement(df, periods):
    def color_rendement(val):
        color = 'green' if float(val) > 0 else ('red' if float(val) < 0 else 'black')
        return f'color: {color}'
    return df.style.map(color_rendement, subset=[f"{p} mois" for p in periods])