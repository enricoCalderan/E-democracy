import google.generativeai as genai
import streamlit as st
import os

# --- CONFIGURAZIONE GEMINI ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    api_key = os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

# --- DATI SIMULATI PROPOSTE DI LEGGE ---
PROPOSTE_LEGGE = [
    {"id": 1, "titolo": "Riforma del Codice della Strada", "area": "Diritto", "desc": "Inasprimento pene per guida al cellulare."},
    {"id": 2, "titolo": "DL 123 - Riforma Digitale PA", "area": "Tecnologia", "desc": "Incentivi per l'adozione dell'AI nella Pubblica Amministrazione."},
    {"id": 3, "titolo": "Tutela Aree Marine Protette", "area": "Ambiente", "desc": "Estensione dei vincoli per la pesca a strascico."},
    {"id": 4, "titolo": "Flat Tax Incrementale", "area": "Economia", "desc": "Nuove aliquote per le partite IVA."},
    {"id": 5, "titolo": "Regolamentazione Droni Urbani", "area": "Tecnologia", "desc": "Norme di sicurezza per il volo in città."}
]