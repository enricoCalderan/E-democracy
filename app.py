import streamlit as st

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(layout="wide", page_title="Portale Partecipazione Legislativa", page_icon="🏛️", initial_sidebar_state="expanded")

# --- STILE ISTITUZIONALE (CSS) ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* 1. STILE GLOBALE PER TUTTI I PULSANTI (Secondary) - BLU SCURO */
    div.stButton > button {
        background-color: #003366 !important;
        color: white !important;
        border: none !important;
        border-radius: 0px !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:hover {
        background-color: #002244 !important;
        color: white !important;
    }

    /* 2. PULSANTI PRIMARI GENERICI (Accedi, Invia, etc.) - BLU CHIARO */
    div.stButton > button[data-testid="stBaseButton-primary"] {
        background-color: #0056b3 !important;
        border: 1px solid #0056b3 !important;
    }

    /* 3. ECCEZIONE: PULSANTI VOTO NON CLICCATI -> BIANCHI */
    /* Usiamo il selettore delle chiavi per isolarli dal resto dell'app */
    div[class*="st-key-vote-"] button, 
    div[class*="st-key-exp-vote-"] button {
        background-color: white !important;
        color: #003366 !important;
        border: 1px solid #003366 !important;
    }
    
    /* 4. FRECCIA SU ATTIVA -> VERDE BOSCO */
    div[class*="vote-up"] button[data-testid="stBaseButton-primary"] {
        background-color: #0b4d17 !important;
        border-color: #0b4d17 !important;
        color: white !important;
        box-shadow: inset 0 4px 6px rgba(0,0,0,0.3) !important;
    }

    /* 5. FRECCIA GIÙ ATTIVA -> ROSSO GRANATA */
    div[class*="vote-down"] button[data-testid="stBaseButton-primary"] {
        background-color: #7a1212 !important;
        border-color: #7a1212 !important;
        color: white !important;
        box-shadow: inset 0 4px 6px rgba(0,0,0,0.3) !important;
    }

    /* Hover specifico per i pulsanti voto per non farli diventare blu scuro */
    div[class*="st-key-vote-"] button:hover {
        background-color: #f0f8ff !important;
        color: #003366 !important;
    }
            
    /* Fascia Tricolore */
    .tricolor-strip {
        height: 4px;
        width: 100%;
        background: linear-gradient(90deg, #009246 33.3%, #ffffff 33.3%, #ffffff 66.6%, #ce2b37 66.6%);
        position: fixed;
        top: 0;
        left: 0;
        z-index: 999999;
    }
</style>
<div class="tricolor-strip"></div>
""", unsafe_allow_html=True)

import ui_login
import ui_cittadino
import ui_relatore

# --- GESTIONE SESSIONE E LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.ruolo = None
    st.session_state.user_info = {}
if 'fase_registrazione' not in st.session_state:
    st.session_state.fase_registrazione = False
    st.session_state.temp_anagrafica = {}
if 'login_step' not in st.session_state:
    st.session_state.login_step = "identificazione" # identificazione, password
if 'temp_user_found' not in st.session_state:
    st.session_state.temp_user_found = None # Dizionario con dati utente trovato

# --- LOGICA PRINCIPALE ---
if not st.session_state.logged_in:
    ui_login.render_login()
else:
    # Sidebar Logout
    with st.sidebar:
        st.markdown("### Profilo Utente")
        if st.session_state.ruolo in ["Cittadino Esperto", "Visualizzatore"]:
            st.markdown(f"**{st.session_state.user_info.get('nome')} {st.session_state.user_info.get('cognome')}**")
            
            if st.session_state.user_info.get('descrizione'):
                st.info(f"_{st.session_state.user_info.get('descrizione')}_")
            
            st.caption(f"Residenza: {st.session_state.user_info.get('citta')}")
            st.caption(f"Età: {st.session_state.user_info.get('eta')} anni")
            
            if st.session_state.ruolo == "Visualizzatore":
                st.info("Profilo Visualizzatore (Sola lettura)")
            else:
                st.success(f"Area Competenza: {st.session_state.user_info.get('area')}")
        elif st.session_state.ruolo == "Relatore":
            st.markdown(f"**On. {st.session_state.user_info.get('cognome')}**")
            st.caption("Camera dei Deputati")
        
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.ruolo = None
            st.session_state.login_step = "identificazione"
            st.session_state.fase_registrazione = False
            st.session_state.user_info = {}
            if 'nav_cittadino' in st.session_state:
                del st.session_state['nav_cittadino']
            st.rerun()

    # --- DASHBOARD CITTADINO ---
    if st.session_state.ruolo in ["Cittadino Esperto", "Visualizzatore"]:
        ui_cittadino.render_dashboard()

    # --- DASHBOARD RELATORE ---
    elif st.session_state.ruolo == "Relatore":
        ui_relatore.render_dashboard()