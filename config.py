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
    {"id": 1, "titolo": "Riforma del Codice della Strada", "area": "Diritto", "desc": "Disegno di legge recante interventi in materia di sicurezza stradale e delega al Governo per la revisione del Codice della strada. Il provvedimento prevede un inasprimento delle sanzioni amministrative e penali per l'utilizzo di dispositivi elettronici alla guida, l'introduzione dell'ergastolo della patente per recidivi in casi di omicidio stradale e nuove norme per la circolazione dei monopattini elettrici, inclusi obbligo di casco e assicurazione."},
    {"id": 2, "titolo": "DL 123 - Riforma Digitale PA", "area": "Tecnologia", "desc": "Decreto Legge per l'accelerazione della transizione digitale nella Pubblica Amministrazione. Il testo introduce l'obbligo di interoperabilità tra le banche dati pubbliche, stanzia fondi per l'adozione di sistemi di Intelligenza Artificiale nei processi amministrativi a basso rischio discrezionale e prevede un piano straordinario di assunzioni per profili tecnici STEM, al fine di ridurre il divario digitale e migliorare l'efficienza dei servizi al cittadino."},
    {"id": 3, "titolo": "Tutela Aree Marine Protette", "area": "Ambiente", "desc": "Proposta di legge quadro per la revisione delle zone di tutela biologica marina. Si prevede l'estensione delle aree a riserva integrale (Zona A) del 20% entro il 2030, il divieto assoluto di pesca a strascico entro le 12 miglia dalla costa nelle aree adiacenti ai parchi marini e l'istituzione di un fondo per la riconversione ecologica delle flotte pescherecce locali, promuovendo attività di ittiturismo e monitoraggio ambientale."},
    {"id": 4, "titolo": "Flat Tax Incrementale", "area": "Economia", "desc": "Introduzione di un regime di tassazione agevolata per le persone fisiche esercenti attività d'impresa, arti o professioni. La norma prevede l'applicazione di un'imposta sostitutiva del 15% sulla differenza tra il reddito d'impresa e di lavoro autonomo determinato nell'anno d'imposta in corso e il reddito più elevato dichiarato nei tre anni precedenti, con un limite massimo di incremento agevolabile pari a 40.000 euro."},
    {"id": 5, "titolo": "Regolamentazione Droni Urbani", "area": "Tecnologia", "desc": "Normativa per l'integrazione dei sistemi aeromobili a pilotaggio remoto (UAS) nello spazio aereo urbano (U-Space). Il testo definisce i corridoi di volo sicuri per il trasporto merci e persone, introduce l'obbligo di identificazione elettronica remota per tutti i droni sopra i 250 grammi e stabilisce standard di rumorosità e sicurezza per le operazioni in aree densamente popolate, con sanzioni severe per le violazioni della privacy."}
]