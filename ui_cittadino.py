import streamlit as st
import pandas as pd
import config
import database as db

def render_dashboard():
    st.title(f"Benvenuto/a, {st.session_state.user_info['nome']}")
    
    if st.session_state.ruolo == "Visualizzatore":
        st.info("ℹ️ Il tuo profilo 'Visualizzatore' ti permette di consultare tutte le proposte e i commenti, ma non di intervenire attivamente.")
        st.divider()
        render_esplora()
    else:
        if 'nav_cittadino' not in st.session_state:
            st.session_state.nav_cittadino = "home"

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
            # Layout centrato con pulsante Indietro isolato a sinistra
            c1, c2, c3 = st.columns([2, 8, 2], vertical_alignment="center")
            with c1:
                if st.button("⬅️ Home", use_container_width=True):
                    st.session_state.nav_cittadino = "home"
                    st.rerun()
            with c2:
                st.markdown("<h2 style='text-align: center; margin: 0; color: #003366;'>Area Partecipazione</h2>", unsafe_allow_html=True)
            st.divider()
            render_partecipa()
            
        elif st.session_state.nav_cittadino == "esplora":
            c1, c2, c3 = st.columns([2, 8, 2], vertical_alignment="center")
            with c1:
                if st.button("⬅️ Home", use_container_width=True):
                    st.session_state.nav_cittadino = "home"
                    st.rerun()
            with c2:
                st.markdown("<h2 style='text-align: center; margin: 0; color: #003366;'>Area Esplorazione</h2>", unsafe_allow_html=True)
            st.divider()
            render_esplora()

def render_partecipa():
    leggi_pertinenti = [p for p in config.PROPOSTE_LEGGE if p['area'] == st.session_state.user_info['area']]
    # Identificativo univoco utente (Nome + Cognome) per evitare conflitti tra omonimi
    autore_corrente = f"{st.session_state.user_info['nome']} {st.session_state.user_info['cognome']}"
    
    if leggi_pertinenti:
        st.subheader("Proposte di legge attive nella tua area")
        legge_selezionata = st.selectbox("Seleziona Proposta:", [p['titolo'] for p in leggi_pertinenti])
        dettaglio_legge = next(p for p in leggi_pertinenti if p['titolo'] == legge_selezionata)
        st.info(f"ℹ️ Descrizione: {dettaglio_legge['desc']}")
        
        # TABS per separare le attività
        tab_parere, tab_voti = st.tabs(["✍️ Il Tuo Parere", "🗳️ Vota Pareri Altrui"])
        
        # --- TAB 1: GESTIONE PARERE PERSONALE ---
        with tab_parere:
            # Verifica parere esistente
            df_pareri = db.get_tutti_pareri()
            testo_precedente = ""
            posizione_precedente = 0
            gia_votato = False
            dati_precedenti = None

            if not df_pareri.empty:
                # Normalizzazione colonne
                if 'Posizione' not in df_pareri.columns: df_pareri['Posizione'] = "Non specificato"
                if 'Autore' not in df_pareri.columns: df_pareri['Autore'] = "Anonimo"

                parere_esistente = df_pareri[(df_pareri['Legge'] == legge_selezionata) & 
                                             (df_pareri['Autore'] == autore_corrente)]
                
                if not parere_esistente.empty:
                    gia_votato = True
                    dati_precedenti = parere_esistente.iloc[0]
                    testo_precedente = dati_precedenti['Parere']
                    pos_str = dati_precedenti['Posizione']
                    opzioni = ["✅ Favorevole", "❌ Contrario", "✏️ Proposta di Modifica"]
                    if pos_str in opzioni:
                        posizione_precedente = opzioni.index(pos_str)

            # UI Stato
            st.divider()
            mostra_form = False

            if gia_votato:
                st.success("**HAI GIÀ PARTECIPATO A QUESTA CONSULTAZIONE**")
                with st.expander("Visualizza il tuo parere attuale", expanded=False):
                    st.write(f"**La tua posizione:** {dati_precedenti['Posizione']}")
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
                with st.form("form_parere"):
                    posizione = st.radio("Posizione:", ["✅ Favorevole", "❌ Contrario", "✏️ Proposta di Modifica"], index=posizione_precedente)
                    testo_parere = st.text_area("Argomentazione / Testo dell'intervento:", value=testo_precedente)
                    
                    if st.form_submit_button(label_btn) and testo_parere:
                        db.salva_parere(legge_selezionata, testo_parere, st.session_state.user_info['area'], posizione, autore_corrente)
                        if gia_votato:
                            st.session_state[f"edit_mode_{legge_selezionata}"] = False
                        st.success("Operazione completata!")
                        st.rerun()
            
            # Storico
            st.divider()
            st.subheader("🗂️ I tuoi interventi passati")
            if not df_pareri.empty and 'Autore' in df_pareri.columns:
                miei = df_pareri[df_pareri['Autore'] == autore_corrente]
                if not miei.empty:
                    st.dataframe(miei[['Legge', 'Posizione', 'Parere']], use_container_width=True, hide_index=True)

        # --- TAB 2: VOTAZIONE ALTRI PARERI ---
        with tab_voti:
            st.subheader("Valuta i pareri della comunità")
            df_pareri = db.get_tutti_pareri()
            
            if not df_pareri.empty:
                # Filtra pareri sulla stessa legge ma di altri autori
                altri_pareri = df_pareri[(df_pareri['Legge'] == legge_selezionata) & 
                                         (df_pareri['Autore'] != autore_corrente)]
                
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
                                st.markdown(f"**{autore_parere}** - *{row.get('Posizione', 'N/A')}*")
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
                                        st.caption(f"💬 **{comm['AutoreCommento']}**: {comm['Testo']}")
                                
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

    else:
        st.warning("Nessuna proposta attiva nella tua area.")

def render_esplora():
    st.subheader("Tutte le proposte in discussione")
    df_pareri = db.get_tutti_pareri()
    autore_corrente = f"{st.session_state.user_info['nome']} {st.session_state.user_info['cognome']}"
    area_utente = st.session_state.user_info['area']
    
    for legge in config.PROPOSTE_LEGGE:
        with st.expander(f"{legge['titolo']} ({legge['area']})"):
            st.write(f"**Descrizione:** {legge['desc']}")
            st.markdown("#### 💬 Dibattito pubblico:")
            if not df_pareri.empty and 'Legge' in df_pareri.columns:
                commenti = df_pareri[df_pareri['Legge'] == legge['titolo']]
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
                                st.markdown(f"**{autore_parere}** - *{row.get('Posizione', 'N/A')}*")
                                st.write(row['Parere'])
                                
                                st.divider()
                                lista_commenti = db.get_commenti_parere(autore_parere, legge['titolo'])
                                
                                commento_precedente = ""
                                if not lista_commenti.empty:
                                    mio_comm = lista_commenti[lista_commenti['AutoreCommento'] == autore_corrente]
                                    if not mio_comm.empty:
                                        commento_precedente = mio_comm.iloc[0]['Testo']
                                    
                                    for _, comm in lista_commenti.iterrows():
                                        st.caption(f"💬 **{comm['AutoreCommento']}**: {comm['Testo']}")
                                
                                with st.expander("Rispondi / Commenta"):
                                    label_comm = "Invia"
                                    if commento_precedente:
                                        label_comm = "Modifica"
                                    testo_comm = st.text_input("Scrivi un commento...", value=commento_precedente, key=f"comm_{idx}")
                                    if st.button(label_comm, key=f"btn_comm_{idx}"):
                                        if testo_comm:
                                            db.salva_commento(autore_corrente, autore_parere, legge['titolo'], testo_comm)
                                            st.rerun()
                else:
                    st.write("Nessun intervento ancora registrato.")