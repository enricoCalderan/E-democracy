import google.generativeai as genai
import streamlit as st
import os

# --- 1. RECUPERO DELLA CHIAVE ---
# Proviamo prima dai secrets di Streamlit, poi dalle variabili d'ambiente
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

st.title("🧪 Test Configurazione Gemini")

if not api_key:
    st.error("🚨 ERRORE: Chiave API non trovata! Assicurati di averla impostata nei Secrets o come variabile d'ambiente.")
    st.stop() # Ferma l'esecuzione se manca la chiave

# --- 2. CONFIGURAZIONE ---
try:
    genai.configure(api_key=api_key)
    # Debug sicuro
    st.info(f"✅ Chiave caricata correttamente: {api_key[:4]}...{api_key[-4:]}")
    
    # --- 3. TEST FUNZIONALE (La prova del nove) ---
    st.subheader("Verifica API in corso...")
    
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Facciamo una domanda semplicissima
    response = model.generate_content("Rispondi solo con la parola 'Funziona!'")
    
    if response.text:
        st.success(f"L'API risponde correttamente: **{response.text}**")
    else:
        st.warning("L'API è configurata ma la risposta è vuota.")

except Exception as e:
    st.error(f"❌ Si è verificato un errore durante la chiamata: {e}")

'''
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)'''