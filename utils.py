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
    Agisci come un esperto AI Engineer e Analista Legislativo di alto livello.
    Il tuo compito è redigere un report tecnico sull'orientamento dei cittadini riguardo alla legge: "{titolo_legge}".

    ### REGOLE RIGOROSE DI ANALISI:
    1. **Filtro Qualitativo:** Analizza ESCLUSIVAMENTE i pareri e i commenti che hanno ricevuto un punteggio positivo (upvotes > downvotes). Ignora i contributi con punteggio nullo o negativo, in quanto privi di consenso da parte della comunità.
    2. **Ponderazione del Consenso:** I pareri con punteggio più alto devono avere un peso proporzionalmente maggiore nella stesura dell'analisi. Devono essere trattati come le istanze prioritarie della cittadinanza.
    3. **Sintesi dei Commenti:** Analizza i fili di discussione (commenti ai pareri). Identifica gli argomenti e le preoccupazioni che ricorrono più spesso nei commenti con votazione positiva e integrali nel report.
    4. **Privacy dei Dati:** NON mostrare mai i punteggi numerici, i voti o i nomi degli utenti nel report finale.
    5. **Terminologia:** Non utilizzare mai la parola "sentiment". Utilizza "Orientamento prevalente", "Clima d'opinione" o "Posizionamento della comunità".

    Genera un report in Markdown strutturato come segue:

    ### Executive Summary
    Descrivi l'orientamento prevalente della comunità verso la proposta di legge, sintetizzando il clima d'opinione generale basato sul peso dei consensi ricevuti.

    ### Analisi del Consenso Prioritario
    Sintesi tecnica dei pareri 'Favorevoli' che godono del maggior supporto. Evidenzia i benefici attesi e le motivazioni di natura economica o sociale che la comunità ritiene fondamentali.

    ### Criticità Costruttive e Dissenso Qualificato
    Analizza i pareri 'Contrari' che hanno comunque ottenuto votazioni positive (critiche ritenute valide dalla comunità). Spiega quali sono i rischi tecnici o i timori procedurali evidenziati, integrando anche i temi ricorrenti emersi dai commenti più apprezzati.

    ### Proposte di Emendamento e Modifica
    Presenta una lista di suggerimenti pratici estratti dai pareri di 'Modifica' con il ranking più alto. Focalizzati sulle soluzioni proposte per migliorare il testo legislativo.

    DATI DI INPUT DA ANALIZZARE:
    {testo_dati}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore durante la generazione del report: {e}"