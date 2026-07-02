import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path


# ========================================
# 1. CHARGEMENT CSS
# ========================================
def load_css(css_path="src/assets/css/streamlit.css"):
    # Charger le fichier CSS pour le style personnalisé
    with open(css_path) as css:
        st.markdown(f"<style>{css.read()}</style>", unsafe_allow_html=True)
 
# ========================================
# 2. COMPOSANTS UI
# ========================================
def display_page_title(title):
    st.markdown(f"""<div class="main-container"><h1>{title}</h1></div>""", unsafe_allow_html=True)

def bout_accueil(back_callback, label="⬅️ Retour à l'accueil"):
    if st.button(label):
        back_callback("home")
        return True
    return False

def footer(text="© 2025 Bastien M. - FinSim — Tous droits réservés."):
    st.markdown(f"""<div class="footer">{text}</div>""", unsafe_allow_html=True)


# ========================================
# 3. GRAPHIQUE INTERACTIF
# ========================================
def display_chart_section(datas_manager, liste_actifs, actif_default, actif_type="indice", color="#6DBE8C"):

    selected_actif = st.selectbox(f"Choisissez un {actif_type} pour le graphique", liste_actifs, index=liste_actifs.index(actif_default) if actif_default in liste_actifs else 0)

    df = datas_manager.get_prix_date(selected_actif)

    if df.empty:
        st.error("Aucune donnée disponible.")
        return

    fig = go.Figure(go.Scatter(x=df["date"], y=df["close"], mode="lines", name=selected_actif, line=dict(color=color, width=2)))

    fig.update_layout(title=f"Évolution de {selected_actif}", xaxis_title="Date", yaxis_title="Prix de clôture", hovermode="x unified")

    st.plotly_chart(fig, use_container_width=True)


# ========================================
# 4. RENDEMENTS
# ========================================
def display_rendement_section(datas_manager, infos_df, liste_actifs, actif_default, calculate_rendement_func, style_rendement_func, actif_type="actif", default_periods=None):

    
    if default_periods is None:
        default_periods = [6, 12, 24, 60, 120, 180]

    # -------------------- INIT SESSION --------------------
    if "periods" not in st.session_state:
        st.session_state.periods = default_periods.copy()

    if "rendement_data" not in st.session_state:
        st.session_state.rendement_data = pd.DataFrame()

    # -------------------- SÉLECTION ACTIFS --------------------
    selected_actifs = st.multiselect(f"Comparer les {actif_type}s", liste_actifs, default=[actif_default] if actif_default in liste_actifs else [])

    st.markdown("---")

    # -------------------- GESTION DES PÉRIODES --------------------
    period_input = st.text_input("Ajouter des périodes (en mois), séparées par des virgules", placeholder="Ex: 1,3,6,12")

    if st.button("➕ Ajouter"):
        try:
            new_periods = [int(p.strip()) for p in period_input.split(",") if p.strip()]
            added = []
            for p in new_periods:
                if p > 0 and p not in st.session_state.periods:
                    st.session_state.periods.append(p)
                    added.append(p)

            if added:
                st.session_state.periods.sort()
                st.session_state.rendement_data = pd.DataFrame()
                st.rerun()
        except ValueError:
            st.error("⚠️ Veuillez entrer uniquement des nombres")

    # Suppression des périodes
    for i in range(0, len(st.session_state.periods), 10):
        cols = st.columns(10, gap="small")
        for idx, p in enumerate(st.session_state.periods[i:i+10]):
            with cols[idx]:
                if st.button(f"❌ {p}m", key=f"remove_{p}", use_container_width=True):
                    st.session_state.periods.remove(p)
                    st.session_state.rendement_data = pd.DataFrame()
                    st.rerun()

    periods = st.session_state.periods
    st.markdown("---")

    # -------------------- CALCUL RENDEMENTS --------------------
    st.session_state.rendement_data = st.session_state.rendement_data.loc[st.session_state.rendement_data.index.intersection(selected_actifs)]

    for actif in selected_actifs:
        expected_cols = [f"{p} mois" for p in periods]
        needs_recalc = (actif not in st.session_state.rendement_data.index or not all(col in st.session_state.rendement_data.columns for col in expected_cols))

        if not needs_recalc:
            continue

        df_prix = datas_manager.get_prix_date(actif)
        if df_prix.empty:
            continue

        df_rend = calculate_rendement_func(df_prix, periods)

        st.session_state.rendement_data = st.session_state.rendement_data.drop(actif, errors="ignore")

        st.session_state.rendement_data = pd.concat([st.session_state.rendement_data, pd.DataFrame(df_rend, index=[actif])])

    # -------------------- AFFICHAGE --------------------
    if not st.session_state.rendement_data.empty and selected_actifs:
        cols_order = [f"{p} mois" for p in periods] 
        cols_order = [c for c in cols_order if c in st.session_state.rendement_data.columns]

        df_display = st.session_state.rendement_data[cols_order].loc[selected_actifs]
        
        # Renommer l'index pour afficher "Indices" en en-tête
        df_display.index.name = actif_type.capitalize() + "s"
        
        styled_df = style_rendement_func(df_display, periods) 
        
        # Configuration pour agrandir la colonne
        column_config = {df_display.index.name: st.column_config.TextColumn(df_display.index.name, width="medium",)}
        
        # Ajout de column_config
        st.dataframe(styled_df, use_container_width=True, column_config=column_config)
    else:
        st.info(f"📊 Sélectionnez des {actif_type}s pour afficher les rendements")


# ========================================
# 5. INFOS ACTIF + COMPOSITION POUR INDICES
# ========================================
def infos_composition_actif(datas_manager, liste_actifs, actif_default, actif_type="indice"):
    
    selected_comp = st.selectbox(f"Choisissez un {actif_type}", liste_actifs, index=liste_actifs.index(actif_default) if actif_default in liste_actifs else 0)

    st.markdown("---")

    df_infos= datas_manager.get_infos_indices(selected_comp)
    
    df_comp = datas_manager.get_composition_indice(selected_comp)
    
    if not df_comp.empty and not df_infos.empty:
        st.subheader("ℹ️ Informations sur l’indice")
        st.dataframe(df_infos, use_container_width=True)

        st.markdown("---")
        
        st.subheader("🧩 Composition de l’indice")
        st.dataframe(df_comp, use_container_width=True)
    else:
        st.info("Aucune donnée disponible.")


# ========================================
# 6. INFOS ACTIF
# ========================================
def infos_actifs(datas_manager, liste_actifs, actif_default, actif_type="actif"):
    # Sélection de l'actif
    selected_comp = st.selectbox(f"Choisissez un {actif_type}", liste_actifs, index=liste_actifs.index(actif_default) if actif_default in liste_actifs else 0)

    # Choix dynamique de la méthode à appeler selon le type d'actif
    if actif_type == "indice":
        if hasattr(datas_manager, "get_infos_indices"):
            df_infos = datas_manager.get_infos_indices(selected_comp)
        else:
            st.error("La méthode get_infos_indices n'existe pas pour ce datas_manager")
            return
    elif actif_type == "crypto":
        if hasattr(datas_manager, "get_infos_cryptos"):
            df_infos = datas_manager.get_infos_cryptos(selected_comp)
        else:
            st.error("La méthode get_infos_cryptos n'existe pas pour ce datas_manager")
            return
    elif actif_type == "stock":
        if hasattr(datas_manager, "get_infos_stocks"):
            df_infos = datas_manager.get_infos_stocks(selected_comp)
        else:
            st.error("La méthode get_infos_stocks n'existe pas pour ce datas_manager")
            return
    elif actif_type == "etf":
        if hasattr(datas_manager, "get_infos_etfs"):
            df_infos = datas_manager.get_infos_etfs(selected_comp)
        else:
            st.error("La méthode get_infos_etfs n'existe pas pour ce datas_manager")
            return
    else:
        st.error("Type d'actif inconnu")
        return

    # Affichage
    if not df_infos.empty:
        st.dataframe(df_infos, use_container_width=True)
    else:
        st.info("Aucune donnée disponible.")



# ========================================  
# 7. TOUS LES ACTIFS RENDEMENTS COMPARATIFS V2
# ========================================

def display_multi_actifs_rendement_section(datas_indices,
                                          datas_stocks,
                                          datas_cryptos,
                                          datas_etfs, 
                                          liste_indices,
                                          liste_stocks,
                                          liste_cryptos,
                                          liste_etfs, 
                                          indice_default,
                                          stock_default,
                                          crypto_default,
                                          etf_default, 
                                          calculate_rendement_func,
                                          style_rendement_func,
                                          default_periods=None):
    
    if default_periods is None:
        default_periods = [6, 12, 24, 60, 120, 180]
    
    # ✅ Clé unique pour cette section
    actif_type = "multi_actifs"
    periods_key = f"periods_{actif_type}"
    rendement_key = f"rendement_data_{actif_type}"
    selected_key = f"selected_{actif_type}"
    weights_key = f"weights_{actif_type}"
    
    # -------------------- INIT SESSION --------------------
    if periods_key not in st.session_state:
        st.session_state[periods_key] = default_periods.copy()
    if rendement_key not in st.session_state:
        st.session_state[rendement_key] = pd.DataFrame()
    
    tous_actifs = set(liste_indices + liste_stocks + liste_cryptos + liste_etfs)
    defaults = [d for d in [indice_default, stock_default, crypto_default, etf_default] if d in tous_actifs]

    if selected_key not in st.session_state:
        st.session_state[selected_key] = defaults
    else:
        actifs_valides = [a for a in st.session_state[selected_key] if a in tous_actifs]
        st.session_state[selected_key] = actifs_valides if actifs_valides else defaults
    
    if weights_key not in st.session_state:
        st.session_state[weights_key] = {
            indice_default: 25.0,
            stock_default: 25.0,
            crypto_default: 25.0,
            etf_default: 25.0  # ⭐ AJOUT
        }
    
    # -------------------- 4 DROPDOWNS --------------------
    st.markdown("""<div class="main-container"><h2>⚖️ Sélectionner les actifs à comparer</h2></div>""", unsafe_allow_html=True)
    st.write("**Sélectionner les actifs à comparer :**")
    
    col1, col2, col3, col4 = st.columns(4)  # ⭐ MODIFIÉ : 4 colonnes
    
    with col1:
        selected_indice = st.selectbox("📈 Indice", liste_indices, 
                                      index=liste_indices.index(indice_default) if indice_default in liste_indices else 0, 
                                      key=f"select_indice_{actif_type}")
        if st.button("➕ Ajouter indice", key=f"add_indice_{actif_type}", use_container_width=True):
            if selected_indice not in st.session_state[selected_key]:
                st.session_state[selected_key].append(selected_indice)
                st.session_state[weights_key][selected_indice] = 0.0
                st.rerun()
    
    with col2:
        selected_stock = st.selectbox("🏢 Entreprise", liste_stocks, 
                                     index=liste_stocks.index(stock_default) if stock_default in liste_stocks else 0, 
                                     key=f"select_stock_{actif_type}")
        if st.button("➕ Ajouter entreprise", key=f"add_stock_{actif_type}", use_container_width=True):
            if selected_stock not in st.session_state[selected_key]:
                st.session_state[selected_key].append(selected_stock)
                st.session_state[weights_key][selected_stock] = 0.0
                st.rerun()
    
    with col3:
        selected_crypto = st.selectbox("₿ Crypto", liste_cryptos, 
                                      index=liste_cryptos.index(crypto_default) if crypto_default in liste_cryptos else 0, 
                                      key=f"select_crypto_{actif_type}")
        if st.button("➕ Ajouter crypto", key=f"add_crypto_{actif_type}", use_container_width=True):
            if selected_crypto not in st.session_state[selected_key]:
                st.session_state[selected_key].append(selected_crypto)
                st.session_state[weights_key][selected_crypto] = 0.0
                st.rerun()
    
    # ⭐ AJOUT : Colonne 4 pour les ETFs
    with col4:
        selected_etf = st.selectbox("💼 ETF", liste_etfs, 
                                   index=liste_etfs.index(etf_default) if etf_default in liste_etfs else 0, 
                                   key=f"select_etf_{actif_type}")
        if st.button("➕ Ajouter ETF", key=f"add_etf_{actif_type}", use_container_width=True):
            if selected_etf not in st.session_state[selected_key]:
                st.session_state[selected_key].append(selected_etf)
                st.session_state[weights_key][selected_etf] = 0.0
                st.rerun()
    
    # -------------------- AFFICHAGE ACTIFS + PONDÉRATIONS --------------------
    st.markdown("""<div class="main-container"><h2>📊 Sélectionner la composition du portefeuille (%)</h2></div>""", unsafe_allow_html=True)
    st.markdown(
    "**- Sélectionner la pondération des actifs sélectionnés pour votre portefeuille.**  \n"
    "**- Les pondérations à 0 % seront ignorées pour le calcul du rendement de votre portefeuille.**")

    
    if st.session_state[selected_key]:
        for actif in st.session_state[selected_key]:
            col_name, col_weight, col_remove = st.columns([3, 2, 1])
            
            with col_name:
                st.write(f"**{actif}**")
            
            with col_weight:
                new_weight = st.number_input(
                    "Poids (%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=st.session_state[weights_key].get(actif, 0.0),
                    step=0.1,
                    key=f"weight_{actif_type}_{actif}",
                    label_visibility="collapsed"
                )
                st.session_state[weights_key][actif] = new_weight
            
            with col_remove:
                if st.button("❌", key=f"remove_actif_{actif_type}_{actif}", type="secondary"):
                    st.session_state[selected_key].remove(actif)
                    del st.session_state[weights_key][actif]
                    st.session_state[rendement_key] = pd.DataFrame()
                    st.rerun()
        
        # Vérification du total des poids
        total_weight = sum(st.session_state[weights_key].values())
        
        if abs(total_weight - 100.0) < 0.01:
            st.success(f"✅ Total : {total_weight:.2f}% (OK)")
        elif total_weight > 100.0:
            st.error(f"❌ Total : {total_weight:.2f}% (dépasse 100%)")
        else:
            st.warning(f"⚠️ Total : {total_weight:.2f}% (inférieur à 100%)")
    else:
        st.info("Aucun actif sélectionné")
    
    # -------------------- GESTION DES PÉRIODES --------------------
    st.markdown("""<div class="main-container"><h2>⏳ Sélectionner les périodes de rendement à analyser</h2></div>""", unsafe_allow_html=True)
    st.markdown( "Ajouter des périodes de rendement (en mois), séparées par des virgules :")

    period_input = st.text_input("Ajouter des périodes de rendement (en mois), séparées par des virgules :", 
                                 placeholder="Ex: 1,3,6,12", 
                                 key=f"period_input_{actif_type}",
                                 label_visibility="collapsed",) # Label masqué
    
    if st.button("➕ Ajouter", key=f"add_period_{actif_type}"):
        try:
            new_periods = [int(p.strip()) for p in period_input.split(",") if p.strip()]
            added = []
            for p in new_periods:
                if p > 0 and p not in st.session_state[periods_key]:
                    st.session_state[periods_key].append(p)
                    added.append(p)
            if added:
                st.session_state[periods_key].sort()
                st.session_state[rendement_key] = pd.DataFrame()
                st.rerun()
        except ValueError:
            st.error("⚠️ Veuillez entrer uniquement des nombres")
    
    # Affichage et suppression des périodes
    for i in range(0, len(st.session_state[periods_key]), 10):
        batch = st.session_state[periods_key][i:i+10]
        cols = st.columns(10, gap="small")
        for idx, p in enumerate(batch):
            with cols[idx]:
                if st.button(f"❌ {p}m", key=f"remove_period_{actif_type}_{p}", use_container_width=True):
                    st.session_state[periods_key].remove(p)
                    st.session_state[rendement_key] = pd.DataFrame()
                    st.rerun()
    
    periods = st.session_state[periods_key]
    selected_actifs = st.session_state[selected_key]
    
    # -------------------- CALCUL RENDEMENTS --------------------
    st.session_state[rendement_key] = st.session_state[rendement_key].loc[
        st.session_state[rendement_key].index.intersection(selected_actifs)
    ]
    
    for actif in selected_actifs:
        expected_cols = [f"{p} mois" for p in periods]
        needs_recalc = (actif not in st.session_state[rendement_key].index or 
                       not all(col in st.session_state[rendement_key].columns for col in expected_cols))
        
        if not needs_recalc:
            continue
        
        # ⭐ MODIFIÉ : Déterminer quelle base de données utiliser (+ ETFs)
        if actif in liste_indices:
            df_prix = datas_indices.get_prix_date(actif)
        elif actif in liste_stocks:
            df_prix = datas_stocks.get_prix_date(actif)
        elif actif in liste_cryptos:
            df_prix = datas_cryptos.get_prix_date(actif)
        elif actif in liste_etfs: 
            df_prix = datas_etfs.get_prix_date(actif)
        else:
            continue
        
        if df_prix.empty:
            continue
        
        df_rend = calculate_rendement_func(df_prix, periods)
        st.session_state[rendement_key] = st.session_state[rendement_key].drop(actif, errors="ignore")
        st.session_state[rendement_key] = pd.concat([st.session_state[rendement_key], pd.DataFrame(df_rend, index=[actif])])
    
    # ✅ CALCUL DU PORTEFEUILLE PONDÉRÉ
    if not st.session_state[rendement_key].empty and selected_actifs:
        portfolio_rendement = {}
        
        for period in periods:
            col_name = f"{period} mois"
            if col_name in st.session_state[rendement_key].columns:
                weighted_sum = 0.0
                for actif in selected_actifs:
                    if actif in st.session_state[rendement_key].index:
                        rendement_val = st.session_state[rendement_key].loc[actif, col_name]
                        try:
                            rendement_float = float(rendement_val)
                            weight = st.session_state[weights_key].get(actif, 0.0) / 100.0
                            weighted_sum += rendement_float * weight
                        except (ValueError, TypeError):
                            pass
                
                portfolio_rendement[col_name] = f"{weighted_sum:.2f}"
        
        # Ajouter le portefeuille au DataFrame
        if portfolio_rendement:
            st.session_state[rendement_key] = st.session_state[rendement_key].drop("📊 PORTEFEUILLE 📊", errors="ignore")
            st.session_state[rendement_key] = pd.concat([
                st.session_state[rendement_key], 
                pd.DataFrame(portfolio_rendement, index=["📊 PORTEFEUILLE 📊"])
            ])
    
    # -------------------- AFFICHAGE DATAFRAME --------------------
    st.markdown("""<div class="main-container"><h2>📈 Tableau récapitulatif des rendements par période</h2></div>""", unsafe_allow_html=True)
    st.write("**Tableau des rendements des actifs sélectionnés et de votre portefeuille :**")
    
    if not st.session_state[rendement_key].empty and selected_actifs:
        cols_order = [f"{p} mois" for p in periods]
        cols_order = [c for c in cols_order if c in st.session_state[rendement_key].columns]
        actifs_valides = [a for a in selected_actifs if a in st.session_state[rendement_key].index]
        if "📊 PORTEFEUILLE 📊" in st.session_state[rendement_key].index:
            actifs_valides.append("📊 PORTEFEUILLE 📊")
        df_display = st.session_state[rendement_key][cols_order].loc[actifs_valides]
        
        df_display.index.name = "Actifs"
        styled_df = style_rendement_func(df_display, periods)
        column_config = {df_display.index.name: st.column_config.TextColumn(df_display.index.name, width="medium")}
        st.dataframe(styled_df, use_container_width=True, column_config=column_config)
    else:
        st.info("📊 Sélectionnez des actifs pour afficher les rendements")