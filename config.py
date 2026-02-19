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