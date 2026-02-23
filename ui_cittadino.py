import streamlit as st
import pandas as pd
import config
import database as db

def render_dashboard():
    st.markdown(f"<h1 style='text-align: center;'>Benvenuto/a, {st.session_state.user_info['nome']}</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #666;'>Area di Competenza: {st.session_state.user_info['area']}</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Per ulteriori informazioni, visita la pagina ufficiale: <a href='https://www.parlamento.it/home' target='_blank'>Parlamento Italiano</a></p>", unsafe_allow_html=True)
    
    if st.session_state.ruolo == "Visualizzatore":
        st.info("ℹ️ Il tuo profilo 'Visualizzatore' ti permette di consultare tutte le proposte e i commenti, ma non di intervenire attivamente.")
        st.divider()
        render_esplora()
    else:
        if 'nav_cittadino' not in st.session_state:
            st.session_state.nav_cittadino = "home"

        if st.session_state.nav_cittadino != "home":
            c_back, _ = st.columns([1, 5])
            with c_back:
                if st.button("⬅️ Torna alla Home"):
                    st.session_state.nav_cittadino = "home"
                    st.rerun()

        if st.session_state.nav_cittadino == "home":
            st.markdown("### Pannello di Controllo")
            st.write("Seleziona un'attività per iniziare:")
            st.write("")
            
            col1, col2 = st.columns(2)
            
            with col1:
                with st.container(border=True):
                    st.markdown("### 📝 Partecipa")
                    st.markdown("Contribuisci attivamente alle proposte di legge della tua area di competenza.")
                    st.write("")
                    if st.button("Vai a Partecipazione", use_container_width=True):
                        st.session_state.nav_cittadino = "partecipa"
                        st.rerun()
            
            with col2:
                with st.container(border=True):
                    st.markdown("### 👀 Esplora")
                    st.markdown("Consulta tutte le proposte, leggi i dibattiti e valuta i pareri degli altri esperti.")
                    st.write("")
                    if st.button("Vai a Esplorazione", use_container_width=True):
                        st.session_state.nav_cittadino = "esplora"
                        st.rerun()

        elif st.session_state.nav_cittadino == "partecipa":
            st.markdown("<h2 style='text-align: center; margin: 0; color: #003366;'>Partecipa</h2>", unsafe_allow_html=True)
            st.divider()
            render_partecipa()
            
        elif st.session_state.nav_cittadino == "esplora":
            st.markdown("<h2 style='text-align: center; margin: 0; color: #003366;'>Esplora</h2>", unsafe_allow_html=True)
            st.divider()
            render_esplora()

def render_partecipa():
    proposte = db.get_proposte_legge()
    leggi_pertinenti = [p for p in proposte if p['area'] == st.session_state.user_info['area']]
    # Identificativo univoco utente (Nome + Cognome) per evitare conflitti tra omonimi
    autore_corrente = f"{st.session_state.user_info['nome']} {st.session_state.user_info['cognome']}"
    
    if leggi_pertinenti:
        st.subheader("Proposte di legge attive nella tua area")
        legge_selezionata = st.selectbox("Seleziona Proposta:", [p['titolo'] for p in leggi_pertinenti], index=None, placeholder="Scegli una proposta...")
        
        if not legge_selezionata:
            st.info("Seleziona una proposta dal menu in alto per visualizzare i dettagli e partecipare.")
        else:
            dettaglio_legge = next(p for p in leggi_pertinenti if p['titolo'] == legge_selezionata)
            with st.container(border=True):
                st.markdown(f"<div style='text-align: justify; font-family: serif; font-size: 1.1em; line-height: 1.6;'>{dettaglio_legge['desc']}</div>", unsafe_allow_html=True)
            
            # TABS per separare le attività
            tab_parere, tab_voti = st.tabs(["✍️ Il Tuo Parere", "🗳️ Vota Pareri Altrui"])
            
            # --- TAB 1: GESTIONE PARERE PERSONALE ---
            with tab_parere:
                # Verifica parere esistente
                df_pareri = db.get_tutti_pareri()
                testo_precedente = ""
                posizione_precedente = 0
                giudizio_precedente = "Buono" # Default
                gia_votato = False
                dati_precedenti = None

                if not df_pareri.empty:
                    # Normalizzazione colonne
                    if 'Posizione' not in df_pareri.columns: df_pareri['Posizione'] = "Non specificato"
                    if 'Autore' not in df_pareri.columns: df_pareri['Autore'] = "Anonimo"
                    if 'Giudizio' not in df_pareri.columns: df_pareri['Giudizio'] = "Buono"

                    parere_esistente = df_pareri[(df_pareri['Legge'] == legge_selezionata) & 
                                                 (df_pareri['Autore'] == autore_corrente)]
                    
                    if not parere_esistente.empty:
                        gia_votato = True
                        dati_precedenti = parere_esistente.iloc[0]
                        testo_precedente = dati_precedenti['Parere']
                        pos_str = dati_precedenti['Posizione']
                        giudizio_precedente = dati_precedenti.get('Giudizio', "Buono")
                        opzioni = ["✅ Favorevole", "❌ Contrario"]
                        if pos_str in opzioni:
                            posizione_precedente = opzioni.index(pos_str)

                # UI Stato
                st.divider()
                mostra_form = False

                if gia_votato:
                    st.success("**HAI GIÀ PARTECIPATO A QUESTA CONSULTAZIONE**")
                    with st.expander("Visualizza il tuo parere attuale", expanded=False):
                        st.write(f"**La tua posizione:** {dati_precedenti['Posizione']}")
                        st.write(f"**Giudizio Maggioritario:** {dati_precedenti.get('Giudizio', 'N/A')}")
                        st.write(f"**Il tuo commento:** {dati_precedenti['Parere']}")
                    
                    # Gestione stato modifica
                    edit_key = f"edit_mode_{legge_selezionata}"
                    if st.session_state.get(edit_key, False):
                        if st.button("Annulla Modifica"):
                            st.session_state[edit_key] = False
                            st.rerun()
                        mostra_form = True
                        st.subheader("✏️ Modifica il tuo intervento")
                        label_btn = "Aggiorna Parere"
                    else:
                        if st.button("Modifica il tuo parere"):
                            st.session_state[edit_key] = True
                            st.rerun()
                else:
                    st.info("**NON HAI ANCORA ESPRESSO UN PARERE**")
                    st.subheader("📝 Inserisci il tuo intervento")
                    mostra_form = True
                    label_btn = "Invia al Parlamento"

                if mostra_form:
                    # Rimosso st.form per permettere interattività dinamica
                    st.markdown("##### 1. Orientamento Generale")
                    
                    # Opzioni posizione
                    opzioni_pos = ["✅ Favorevole", "❌ Contrario"]
                    
                    # Gestione stato widget per interattività
                    key_pos = f"radio_pos_{legge_selezionata}"
                    if key_pos not in st.session_state:
                        st.session_state[key_pos] = opzioni_pos[posizione_precedente]
                    
                    posizione = st.radio("Esprimi il tuo voto:", opzioni_pos, key=key_pos, horizontal=True)
                    
                    st.markdown("##### 2. Giudizio Maggioritario (Obbligatorio)")
                    st.caption("Valuta la qualità complessiva della proposta. Le opzioni variano in base al tuo orientamento.")
                    
                    # Logica condizionale per le opzioni del giudizio
                    if "Favorevole" in posizione:
                        scala_giudizio = ['Ottimo', 'Molto Buono', 'Buono', 'Passabile']
                        colore_box = "#e6fffa" # Sfondo verdino
                    else:
                        scala_giudizio = ['Mediocre', 'Rifiuto']
                        colore_box = "#fff5f5" # Sfondo rossiccio
                    
                    # Calcolo valore default coerente
                    valore_default = scala_giudizio[0]
                    if giudizio_precedente in scala_giudizio:
                        valore_default = giudizio_precedente
                    
                    # Aspetto grafico modificato con container colorato
                    with st.container():
                        st.markdown(f"<div style='background-color: {colore_box}; padding: 15px; border-radius: 10px; border: 1px solid #ddd;'>", unsafe_allow_html=True)
                        giudizio = st.select_slider("Seleziona il livello di gradimento:", options=scala_giudizio, value=valore_default, key=f"slider_{legge_selezionata}")
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("##### 3. Motivazione Tecnica (Opzionale)")
                    st.caption("Puoi lasciare questo campo vuoto se vuoi esprimere solo il voto.")
                    testo_parere = st.text_area("Argomentazione / Testo dell'intervento:", value=testo_precedente)
                    
                    st.write("")
                    # Pulsante invio (ora accetta anche testo vuoto)
                    if st.button(label_btn, type="primary", use_container_width=True):
                        db.salva_parere(legge_selezionata, testo_parere, st.session_state.user_info['area'], posizione, autore_corrente, giudizio)
                        if gia_votato:
                            st.session_state[f"edit_mode_{legge_selezionata}"] = False
                        st.success("Operazione completata!")
                        st.rerun()

            # --- TAB 2: VOTAZIONE ALTRI PARERI ---
            with tab_voti:
                st.subheader("Valuta i pareri della comunità")
                df_pareri = db.get_tutti_pareri()
                
                if not df_pareri.empty:
                    # Filtra pareri sulla stessa legge ma di altri autori
                    altri_pareri = df_pareri[(df_pareri['Legge'] == legge_selezionata) & 
                                             (df_pareri['Autore'] != autore_corrente)]
                    
                    # FILTRO: Mostra solo pareri con testo (esclude voti silenziosi)
                    altri_pareri = altri_pareri[altri_pareri['Parere'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)]

                    if not altri_pareri.empty:
                        for idx, row in altri_pareri.iterrows():
                            with st.container(border=True):
                                col_voto, col_contenuto = st.columns([1, 5])
                                
                                autore_parere = row['Autore']
                                
                                with col_voto:
                                    score = db.get_punteggio_parere(autore_parere, legge_selezionata)
                                    st.metric("Valutazione", score)
                                    
                                    # Recupera il voto attuale dell'utente per colorare i bottoni
                                    voto_attuale = db.get_voto_utente(autore_corrente, autore_parere, legge_selezionata)
                                    # Selezionato = Primary (Verde), Non selezionato = Secondary (Outline)
                                    type_up = "primary" if voto_attuale == 1 else "secondary"
                                    type_down = "primary" if voto_attuale == -1 else "secondary"

                                    # Pulsanti Voto
                                    c1, c2 = st.columns(2)
                                    if c1.button("⬆️", key=f"vote-up-{idx}", type=type_up):
                                        db.salva_voto(autore_corrente, autore_parere, legge_selezionata, 1)
                                        st.rerun()
                                    if c2.button("⬇️", key=f"vote-down-{idx}", type=type_down):
                                        db.salva_voto(autore_corrente, autore_parere, legge_selezionata, -1)
                                        st.rerun()
                                
                                with col_contenuto:
                                    st.markdown(f"**Utente Esperto** - *{row.get('Posizione', 'N/A')}*")
                                    st.write(row['Parere'])
                                    
                                    # --- SEZIONE COMMENTI ---
                                    st.divider()
                                    commenti = db.get_commenti_parere(autore_parere, legge_selezionata)
                                    
                                    commento_precedente = ""
                                    if not commenti.empty:
                                        mio_comm = commenti[commenti['AutoreCommento'] == autore_corrente]
                                        if not mio_comm.empty:
                                            commento_precedente = mio_comm.iloc[0]['Testo']
                                        
                                        for _, comm in commenti.iterrows():
                                            st.caption(f"💬 **Utente**: {comm['Testo']}")
                                    
                                    with st.expander("Rispondi / Commenta"):
                                        label_comm = "Invia"
                                        if commento_precedente:
                                            label_comm = "Modifica"
                                        testo_comm = st.text_input("Scrivi un commento...", value=commento_precedente, key=f"comm_{idx}")
                                        if st.button(label_comm, key=f"btn_comm_{idx}"):
                                            if testo_comm:
                                                db.salva_commento(autore_corrente, autore_parere, legge_selezionata, testo_comm)
                                                st.rerun()
                    else:
                        st.info("Non ci sono ancora pareri di altri utenti su questa legge.")
                else:
                    st.info("Nessun dato disponibile.")

        # --- STORICO INTERVENTI (Sempre visibile) ---
        st.divider()
        st.subheader("🗂️ I tuoi interventi passati")
        df_pareri_all = db.get_tutti_pareri()
        if not df_pareri_all.empty and 'Autore' in df_pareri_all.columns:
            miei = df_pareri_all[df_pareri_all['Autore'] == autore_corrente].copy()
            if not miei.empty:
                # Calcolo punteggio per ogni parere
                miei['Voti'] = miei.apply(lambda x: db.get_punteggio_parere(x['Autore'], x['Legge']), axis=1)
                st.dataframe(miei[['Legge', 'Posizione', 'Parere', 'Voti']], use_container_width=True, hide_index=True)
            else:
                st.write("Non hai ancora effettuato interventi.")
        else:
            st.write("Nessun dato disponibile.")

    else:
        st.warning("Nessuna proposta attiva nella tua area.")

def render_esplora():
    st.subheader("Tutte le proposte in discussione")
    df_pareri = db.get_tutti_pareri()
    autore_corrente = f"{st.session_state.user_info['nome']} {st.session_state.user_info['cognome']}"
    area_utente = st.session_state.user_info['area']
    proposte = db.get_proposte_legge()
    
    for legge in proposte:
        with st.expander(f"{legge['titolo']} ({legge['area']})"):
            st.markdown(f"<div style='text-align: justify; font-family: serif; font-size: 1.05em; padding: 10px; background-color: #f8f9fa; border-left: 4px solid #003366; margin-bottom: 15px;'>{legge['desc']}</div>", unsafe_allow_html=True)
            st.markdown("#### 💬 Dibattito pubblico:")
            if not df_pareri.empty and 'Legge' in df_pareri.columns:
                commenti = df_pareri[df_pareri['Legge'] == legge['titolo']]
                # FILTRO: Mostra solo pareri con testo
                commenti = commenti[commenti['Parere'].apply(lambda x: isinstance(x, str) and len(x.strip()) > 0)]
                
                if not commenti.empty:
                    for idx, row in commenti.iterrows():
                        with st.container(border=True):
                            col_voto, col_contenuto = st.columns([1, 5])
                            autore_parere = row['Autore']
                            
                            with col_voto:
                                score = db.get_punteggio_parere(autore_parere, legge['titolo'])
                                st.metric("Valutazione", score)
                                
                                voto_attuale = db.get_voto_utente(autore_corrente, autore_parere, legge['titolo'])
                                type_up = "primary" if voto_attuale == 1 else "secondary"
                                type_down = "primary" if voto_attuale == -1 else "secondary"

                                # Voto abilitato solo se l'area coincide E l'utente non è un visualizzatore
                                can_vote = (legge['area'] == area_utente) and (st.session_state.ruolo != "Visualizzatore")

                                c1, c2 = st.columns(2)
                                if c1.button("⬆️", key=f"exp-vote-up-{idx}", type=type_up, disabled=not can_vote):
                                    db.salva_voto(autore_corrente, autore_parere, legge['titolo'], 1)
                                    st.rerun()
                                if c2.button("⬇️", key=f"exp-vote-down-{idx}", type=type_down, disabled=not can_vote):
                                    db.salva_voto(autore_corrente, autore_parere, legge['titolo'], -1)
                                    st.rerun()
                                if not can_vote:
                                    if st.session_state.ruolo == "Visualizzatore":
                                        st.caption("🔒 Sola lettura")
                                    else:
                                        st.caption("🔒 Solo esperti")
                            
                            with col_contenuto:
                                st.markdown(f"**Utente Esperto** - *{row.get('Posizione', 'N/A')}*")
                                st.write(row['Parere'])
                                
                                st.divider()
                                lista_commenti = db.get_commenti_parere(autore_parere, legge['titolo'])
                                
                                commento_precedente = ""
                                if not lista_commenti.empty:
                                    mio_comm = lista_commenti[lista_commenti['AutoreCommento'] == autore_corrente]
                                    if not mio_comm.empty:
                                        commento_precedente = mio_comm.iloc[0]['Testo']
                                    
                                    for _, comm in lista_commenti.iterrows():
                                        st.caption(f"💬 **Utente**: {comm['Testo']}")
                                
                                with st.expander("Rispondi / Commenta"):
                                    if can_vote:
                                        label_comm = "Invia"
                                        if commento_precedente:
                                            label_comm = "Modifica"
                                        testo_comm = st.text_input("Scrivi un commento...", value=commento_precedente, key=f"comm_{idx}")
                                        if st.button(label_comm, key=f"btn_comm_{idx}"):
                                            if testo_comm:
                                                db.salva_commento(autore_corrente, autore_parere, legge['titolo'], testo_comm)
                                                st.rerun()
                                    else:
                                        st.info(f"🔒 Solo gli esperti dell'area **{legge['area']}** possono commentare.")
                else:
                    st.write("Nessun intervento ancora registrato.")