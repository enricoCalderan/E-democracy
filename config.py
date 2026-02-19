import google.generativeai as genai
import streamlit as st
import os

# --- CONFIGURAZIONE GEMINI ---
# DEBUG TEMPORANEO (Rimuovilo dopo il test!)
if not api_key:
    st.error("🚨 ERRORE: La variabile api_key è vuota!")
else:
    # Mostriamo solo i primi e gli ultimi 3 caratteri per sicurezza
    st.write(f"DEBUG: Chiave caricata: {api_key[:4]}...{api_key[-3:]}")
    st.write(f"DEBUG: Lunghezza chiave: {len(api_key)}")

'''
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)'''