import streamlit as st
import database as db
import utils
import os

def render_login():
    if 'show_privacy' not in st.session_state:
        st.session_state.show_privacy = False
    if st.session_state.show_privacy:
        render_privacy_page()
        return

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
                                    st.session_state.privacy_accepted = False
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
        if not st.session_state.get('privacy_accepted', False):
            st.markdown("### Richiesta Consenso Privacy")
            st.warning("Per procedere con la registrazione, è necessario leggere e accettare l'informativa sul trattamento dei dati personali.")
            render_privacy_text()
            st.divider()
            c1, c2 = st.columns(2)
            if c1.button("Rifiuto", use_container_width=True):
                st.session_state.fase_registrazione = False
                st.session_state.privacy_accepted = False
                st.rerun()
            if c2.button("Ho letto e Accetto", type="primary", use_container_width=True):
                st.session_state.privacy_accepted = True
                st.rerun()
            return

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

    # --- FOOTER PRIVACY ---
    st.divider()
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        if st.button("🔒 Informativa Privacy e Trattamento Dati", use_container_width=True):
            st.session_state.show_privacy = True
            st.rerun()

def render_privacy_text():
    st.markdown("## Informativa sul Trattamento dei Dati Personali")
    st.caption("Ultimo aggiornamento: 19 Febbraio 2026")
    
    st.markdown("""
    ### Premessa e Riferimenti Normativi
    La presente piattaforma di Analisi Legislativa si impegna a proteggere la privacy degli utenti e a garantire la trasparenza nel trattamento dei dati. La presente informativa è redatta in conformità a:
    - **Regolamento (UE) 2016/679** (Regolamento Generale sulla Protezione dei Dati - GDPR).
    - **D.Lgs. 196/2003** (Codice in materia di protezione dei dati personali), come modificato dal D.Lgs. 101/2018.
    - **Regolamento (UE) 2024/1689** (Artificial Intelligence Act), con particolare riferimento agli obblighi di trasparenza per i sistemi di IA generativa.

    ### 1. Titolare del Trattamento
    Il trattamento dei dati è finalizzato esclusivamente alla ricerca statistica e all'analisi del consenso in ambito legislativo. Il Titolare garantisce che i dati non saranno ceduti a terzi per scopi commerciali. Per qualsiasi richiesta (accesso, rettifica o cancellazione), contattare:
    
    **Referente Privacy:** Enrico Calderan
    **Email:** admin@progetto.it

    ### 2. Tipologia di Dati Raccolti
    La piattaforma raccoglie le seguenti categorie di dati:
    - **Dati di Opinione:** Orientamento (Favorevole/Contrario), Giudizio Maggioritario (scala da Ottimo a Rifiuto) e commenti testuali.
    - **Dati Professionali (CV):** Informazioni caricate volontariamente dall'utente in formato PDF, processate per identificare l'area di competenza e la seniority.
    - **Dati Tecnici:** Indirizzo IP, timestamp e log di sessione, necessari per garantire la sicurezza del sistema e prevenire votazioni multiple fraudolente.

    ### 3. Base Giuridica del Trattamento
    Ai sensi dell'Art. 6 del GDPR, il trattamento dei dati si fonda sul **Consenso Esplicito dell'Interessato**. L'utente esprime il proprio consenso interagendo con la piattaforma, effettuando il login e accettando i termini prima del caricamento di qualsiasi documento (CV) o dell'invio di pareri.

    ### 4. Utilizzo dell'Intelligenza Artificiale (AI Act)
    In conformità con l'AI Act (UE 2024/1689), si informa l'utente che:
    - I testi dei pareri e i contenuti dei CV sono analizzati tramite il modello **Google Gemini API**.
    - I dati vengono inviati ai server di Google in forma pseudonimizzata.
    - Il sistema effettua un'analisi automatizzata per categorizzare le competenze, ma **non adotta decisioni automatizzate** che producano effetti giuridici significativi senza la supervisione di un analista umano (il Relatore).
    - I dati forniti non vengono utilizzati da Google per l'addestramento dei propri modelli globali (Enterprise Privacy Policy).

    ### 5. Finalità e Modalità del Trattamento
    I dati vengono trattati esclusivamente per:
    - **Analisi Legislativa:** Generare report di sintesi per i parlamentari e i relatori delle proposte di legge.
    - **Ponderazione del Consenso:** Calcolare il peso delle opinioni in base al profilo professionale dell'utente.
    - **Visualizzazione:** Alimentare i grafici sul Giudizio Maggioritario nelle dashboard istituzionali.

    ### 6. Conservazione dei Dati e Cookie Policy
    - **Conservazione:** I dati saranno conservati per il tempo strettamente necessario al raggiungimento delle finalità di ricerca o fino alla richiesta di cancellazione da parte dell'utente.
    - **Cookie:** L'applicazione utilizza solo cookie tecnici (essenziali per il funzionamento di Streamlit e la gestione della sessione). Non sono presenti cookie di profilazione o di tracciamento pubblicitario.

    ### 7. Diritti dell'Interessato
    In ogni momento, ai sensi degli Artt. 15-22 del GDPR, l'utente può esercitare il diritto di:
    - Ottenere la conferma dell'esistenza dei propri dati.
    - Richiedere la rettifica o la cancellazione totale (Diritto all'Oblio).
    - Opporsi al trattamento per motivi legittimi.
    - Proporre reclamo all'Autorità Garante per la Protezione dei Dati Personali.

    **Dichiarazione di Consenso:** Proseguendo con l'utilizzo della piattaforma e cliccando sui pulsanti di invio, l'utente dichiara di aver preso visione della presente informativa e acconsente al trattamento dei propri dati secondo le modalità descritte.
    """)
    
def render_privacy_page():
    render_privacy_text()
    st.divider()
    if st.button("⬅️ Torna alla Home", use_container_width=True):
        st.session_state.show_privacy = False
        st.rerun()