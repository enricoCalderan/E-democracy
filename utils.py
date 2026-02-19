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

def genera_sintesi_legislativa(lista_pareri, titolo_legge):
    """
    Genera un report di sintesi legislativa pesato sui voti dei pareri.
    lista_pareri: lista di dizionari {Testo, Posizione, Punteggio}
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Conversione dati in stringa per il prompt
    testo_dati = ""
    for p in lista_pareri:
        testo_dati += f"- [Punteggio: {p['Punteggio']}] Posizione: {p['Posizione']} | Contenuto: {p['Testo']}\n"

    prompt = f"""
    Agisci come un esperto AI Engineer e Analista Legislativo.
    Analizza i seguenti pareri cittadini sulla legge: "{titolo_legge}".
    
    I pareri sono forniti con un 'Punteggio' (voti up/down). 
    ISTRUZIONE CHIAVE: I pareri con punteggio più alto rappresentano il consenso della comunità e devono influenzare maggiormente la sintesi.
    
    Genera un report strutturato in Markdown con queste sezioni esatte:
    
    ### Executive Summary
    Un'analisi generale del sentiment basata sul peso dei voti.
    
    ### Consenso ad alto impatto
    Sintesi dei pareri 'Favorevole' che hanno ricevuto più approvazione, evidenziando i punti di forza tecnici.
    
    ### Dissenso Qualificato
    Analisi delle critiche (pareri 'Contrario') più votate, spiegando quali sono i rischi principali rilevati dagli esperti.
    
    ### Proposte di Emendamento
    Una lista di suggerimenti pratici estratti dai pareri (specie quelli di 'Modifica') con il ranking più alto.
    
    DATI INPUT (Ordinati per rilevanza):
    {testo_dati}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore durante la generazione del report: {e}"