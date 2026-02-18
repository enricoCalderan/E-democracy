from PyPDF2 import PdfReader
import google.generativeai as genai
import streamlit as st
import config # Importa la configurazione per assicurarsi che genai sia configurato

def analizza_testo_pdf(file):
    reader = PdfReader(file)
    testo = "".join([page.extract_text() for page in reader.pages])
    return testo

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Analizza questo CV.
    1. Identifica l'area di competenza principale tra: Tecnologia, Diritto, Ambiente, Economia.
       Se il candidato non ha competenze specifiche in queste aree o è uno studente senza specializzazione, scrivi 'Nessuna'.
    2. Scrivi una breve descrizione professionale del candidato in terza persona (max 25 parole).
    
    Restituisci il risultato in questo formato esatto:
    Area: [Area scelta]
    Descrizione: [Breve descrizione]
    
    Testo: {testo_cv[:3000]}
    """
    try:
        response = model.generate_content(prompt)
        text = response.text
        area = text.split("Area:")[1].split("Descrizione:")[0].strip()
        descrizione = text.split("Descrizione:")[1].strip()
        return area, descrizione
    except Exception as e:
        st.error(f"Errore specifico AI: {e}")
        return None, None