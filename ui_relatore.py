import streamlit as st
import pandas as pd
import plotly.express as px
import database as db
import utils

def render_dashboard():
    # Recupera la legge assegnata (salvata nel campo 'area' durante il login)
    legge_assegnata = st.session_state.user_info['area']
    
    st.markdown("## Centro di Comando Legislativo")
    st.markdown(f"### Norma assegnata: {legge_assegnata}")
    st.divider()

    df_pareri = db.get_tutti_pareri()
    
    # Filtra i dati per la legge specifica
    df_legge = pd.DataFrame()
    if not df_pareri.empty and 'Legge' in df_pareri.columns:
        df_legge = df_pareri[df_pareri['Legge'] == legge_assegnata]
        # Normalizzazione colonne
        if 'Posizione' not in df_legge.columns: df_legge['Posizione'] = "Non specificato"

    if not df_legge.empty:
        # --- CALCOLO KPI ---
        totale = len(df_legge)
        favorevoli = len(df_legge[df_legge['Posizione'].str.contains("Favorevole", case=False, na=False)])
        contrari = len(df_legge[df_legge['Posizione'].str.contains("Contrario", case=False, na=False)])
        modifiche = len(df_legge[df_legge['Posizione'].str.contains("Modifica", case=False, na=False)])

        # --- VISUALIZZAZIONE METRICHE ---
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Totale Pareri", totale)
            col2.metric("Favorevoli", favorevoli)
            col3.metric("Contrari", contrari)
            col4.metric("Richieste Modifica", modifiche)

        st.write("")
        
        # --- GRAFICO ANALISI CONSENSO ---
        st.markdown("### Analisi del Consenso")
        
        # Creazione DataFrame per il grafico
        dati_grafico = df_legge['Posizione'].value_counts().reset_index()
        dati_grafico.columns = ['Posizione', 'Conteggio']
        
        # Mappa colori personalizzata
        color_map = {
            "✅ Favorevole": "#28a745",           # Verde
            "❌ Contrario": "#dc3545",            # Rosso
            "✏️ Proposta di Modifica": "#17a2b8"  # Azzurro
        }
        
        fig = px.pie(dati_grafico, values='Conteggio', names='Posizione', hole=0.4, 
                     color='Posizione', color_discrete_map=color_map)
        st.plotly_chart(fig, use_container_width=True)

        # --- SINTESI LEGISLATIVA PESATA (AI) ---
        st.write("")
        st.markdown("### 🧠 Sintesi Legislativa Pesata (AI)")
        
        with st.container(border=True):
            st.markdown("**Analisi automatica del consenso basata sui pareri della comunità.**")
            st.caption("L'algoritmo ordina i pareri per punteggio (voti positivi netti) prima di generare la sintesi.")
            
            if st.button("✨ Genera/Aggiorna Analisi AI", use_container_width=True):
                with st.spinner("L'IA sta analizzando i pareri e calcolando i pesi..."):
                    # 1. Recupero dati e calcolo punteggi
                    dati_ai = []
                    for _, row in df_legge.iterrows():
                        score = db.get_punteggio_parere(row['Autore'], legge_assegnata)
                        dati_ai.append({
                            "Testo": row['Parere'],
                            "Posizione": row['Posizione'],
                            "Punteggio": score
                        })
                    
                    # 2. Ordinamento decrescente per Punteggio
                    dati_ai.sort(key=lambda x: x['Punteggio'], reverse=True)
                    
                    # 3. Generazione Report
                    if dati_ai:
                        report = utils.genera_sintesi_legislativa(dati_ai, legge_assegnata)
                        st.markdown(report)
                    else:
                        st.warning("Nessun parere disponibile per l'analisi.")

        st.markdown("### Dettaglio Contributi")
        
        # Calcolo punteggi e ordinamento
        df_legge = df_legge.copy()
        df_legge['Punteggio'] = df_legge.apply(lambda x: db.get_punteggio_parere(x['Autore'], legge_assegnata), axis=1)
        df_legge = df_legge.sort_values(by='Punteggio', ascending=False)
        
        for idx, row in df_legge.iterrows():
            # Anonimizzazione: non mostriamo l'autore
            with st.expander(f"[Valutazione: {row['Punteggio']}] {row['Posizione']}"):
                st.write(f"**Parere completo:** {row['Parere']}")
                
                commenti = db.get_commenti_parere(row['Autore'], legge_assegnata)
                if not commenti.empty:
                    st.markdown("---")
                    st.markdown("**Commenti:**")
                    for _, comm in commenti.iterrows():
                        st.info(f"**Utente:** {comm['Testo']}")
                else:
                    st.caption("Nessun commento presente.")
    else:
        st.info(f"Non sono ancora presenti pareri o dati per la norma: **{legge_assegnata}**.")