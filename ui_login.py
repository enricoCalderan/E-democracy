import streamlit as st
import database as db
import utils
import os

def render_login():
    st.markdown("<h1 style='text-align: center;'>Portale Partecipazione Legislativa</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Piattaforma istituzionale per il contributo tecnico ai processi decisionali.</p>", unsafe_allow_html=True)
    st.write("")

    if not st.session_state.fase_registrazione:
        col1, col2, col3 = st.columns([1, 1.5, 1])
        with col2:
            # STEP 1: IDENTIFICAZIONE
            if st.session_state.login_step == "identificazione":
                with st.container(border=True):
                    if os.path.exists("Italia-digitale.jpg"):
                        st.image("Italia-digitale.jpg", use_container_width=True)
                    st.markdown("### Accesso Utente")
                    st.caption("Inserisci le credenziali per accedere o registrarti.")
                    st.info("Esempi: **Luigi Verdi** (pass: 1234) | **Matteo Salvini** (pass: admin)")
                    nome = st.text_input("Nome", placeholder="Es. Mario")
                    cognome = st.text_input("Cognome", placeholder="Es. Rossi")
                    
                    st.write("")
                    if st.button("Prosegui", use_container_width=True):
                        if nome and cognome:
                            # 1. Controllo se è un Parlamentare
                            parlamentare = db.get_parlamentare_db(nome, cognome)
                            
                            if parlamentare is not None:
                                st.session_state.temp_user_found = {
                                    "tipo": "Relatore", 
                                    "dati": parlamentare, 
                                    "nome": nome, 
                                    "cognome": cognome
                                }
                                st.session_state.login_step = "password"
                                st.rerun()
                            
                            # 2. Controllo se è un Cittadino
                            else:
                                cittadino = db.get_utente_db(nome, cognome)
                                if cittadino is not None:
                                    st.session_state.temp_user_found = {
                                        "tipo": "Cittadino Esperto", 
                                        "dati": cittadino,
                                        "nome": nome, 
                                        "cognome": cognome
                                    }
                                    st.session_state.login_step = "password"
                                    st.rerun()
                                else:
                                    # 3. Nuovo Cittadino -> Registrazione
                                    st.session_state.temp_anagrafica = {"nome": nome, "cognome": cognome}
                                    st.session_state.fase_registrazione = True
                                    st.rerun()
                        else:
                            st.warning("Inserire nome e cognome per procedere.")

            # STEP 2: PASSWORD
            elif st.session_state.login_step == "password":
                user_data = st.session_state.temp_user_found
                
                if user_data['tipo'] == "Relatore":
                    st.markdown(f"### Area Istituzionale - On. {user_data['cognome']}")
                else:
                    st.markdown(f"### Bentornato, {user_data['nome']}")
                
                password = st.text_input("Inserisci la password", type="password")
                
                if st.button("Accedi", use_container_width=True):
                    # Verifica Password
                    stored_password = str(user_data['dati']['Password'])
                    
                    if password == stored_password:
                        st.session_state.user_info = {
                            "nome": user_data['nome'], 
                            "cognome": user_data['cognome'], 
                            "area": user_data['dati']['Competenza'] if user_data['tipo'] == "Relatore" else user_data['dati']['Area'],
                            "eta": user_data['dati'].get('Eta'),
                            "via": user_data['dati'].get('Indirizzo'),
                            "citta": user_data['dati'].get('Citta'),
                            "descrizione": user_data['dati'].get('Descrizione')
                        }
                        st.session_state.ruolo = user_data['tipo']
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.error("Password errata.")
                
                if st.button("Indietro"):
                    st.session_state.login_step = "identificazione"
                    st.session_state.temp_user_found = None
                    st.rerun()
    
    else:
        # FASE 2: REGISTRAZIONE NUOVO CITTADINO
        st.markdown(f"### Benvenuto {st.session_state.temp_anagrafica['nome']}, completa il profilo")
        st.info("Non risulti registrato nei nostri sistemi. Carica il tuo CV per permettere all'AI di assegnarti un'area di competenza.")
        
        password_reg = st.text_input("Crea una password per i futuri accessi", type="password")
        
        col_a, col_b = st.columns(2)
        with col_a:
            eta = st.number_input("Età", min_value=18, max_value=100, step=1)
        with col_b:
            citta = st.text_input("Città di Residenza")
        via = st.text_input("Indirizzo (Via/Piazza)")
        
        cv_file = st.file_uploader("Carica il tuo CV (PDF)", type="pdf")
        
        if st.button("Analizza CV e Registrati"):
            if cv_file and password_reg and citta and via:
                with st.spinner("Gemini sta analizzando le tue competenze..."):
                    testo_cv = utils.analizza_testo_pdf(cv_file)
                    area_assegnata, descrizione_ai = utils.analizza_cv_con_gemini(testo_cv)
                    
                    if area_assegnata:
                        db.salva_nuovo_utente(st.session_state.temp_anagrafica['nome'], st.session_state.temp_anagrafica['cognome'], area_assegnata, password_reg, eta, via, citta, descrizione_ai)
                        
                        st.session_state.user_info = {
                            "nome": st.session_state.temp_anagrafica['nome'], 
                            "cognome": st.session_state.temp_anagrafica['cognome'], 
                            "area": area_assegnata,
                            "eta": eta, "via": via, "citta": citta, "descrizione": descrizione_ai
                        }
                        st.session_state.ruolo = "Cittadino Esperto"
                        st.session_state.logged_in = True
                        st.rerun()
            else:
                st.error("Compila tutti i campi obbligatori.")