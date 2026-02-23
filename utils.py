from PyPDF2 import PdfReader
import google.generativeai as genai
import streamlit as st
import config # Importa la configurazione per assicurarsi che genai sia configurato
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

def analizza_testo_pdf(file):
    reader = PdfReader(file)
    testo = "".join([page.extract_text() for page in reader.pages])
    return testo

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Agisci come un Senior HR Consultant esperto in analisi tecnica. 
    Analizza il seguente CV con un approccio analitico e formale.
    
    1. Identifica l'area di competenza principale esclusivamente tra: Tecnologia, Diritto, Ambiente, Economia.
       Se il profilo è generico o in fase di formazione senza una specializzazione chiara, scrivi 'Nessuna'.
       
    2. Redigi un profilo professionale sintetico in terza persona (max 15 parole). 
       ISTRUZIONI RIGOROSE: 
       - Mantieni un registro linguistico formale e istituzionale.
       - NON includere il nome proprio, cognome o riferimenti anagrafici della persona.
       - Focalizzati esclusivamente su qualifica, seniority e competenze core.
    
    Restituisci il risultato in questo formato esatto:
    Area: [Area scelta]
    Descrizione: [Profilo professionale formale]
    
    Testo del CV: {testo_cv[:3000]}
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

    DATI DI INPUT DA ANALIZZARE:
    {testo_dati}
    """
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore durante la generazione del report: {e}"

def esegui_clustering_opinioni(df, colonna_testo='Parere'):
    """
    Esegue clustering semantico sui pareri usando Embeddings + KMeans + PCA.
    Restituisce il DataFrame arricchito e il grafico Plotly.
    """
    # 1. Controllo Dati
    if df.empty or len(df) < 3:
        return None, None

    try:
        # 2. Generazione Embeddings (Google text-embedding-004)
        def get_embedding(text):
            if not isinstance(text, str) or not text.strip():
                return np.zeros(768)
            # Task type clustering ottimizza i vettori per il raggruppamento
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text,
                task_type="clustering"
            )
            return result['embedding']

        # Applica la funzione a tutti i pareri
        embeddings = df[colonna_testo].apply(get_embedding).tolist()
        matrix = np.array(embeddings)

        # 3. Clustering (K-Means)
        # Determina dinamicamente il numero di cluster (max 4 o n_samples)
        n_clusters = min(4, len(df))
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(matrix)

        # 4. Riduzione Dimensionale (PCA) per visualizzazione 2D
        pca = PCA(n_components=2)
        components = pca.fit_transform(matrix)
        df['pca_x'] = components[:, 0]
        df['pca_y'] = components[:, 1]

        # 5. Auto-Labeling con Gemini
        model = genai.GenerativeModel('gemini-2.5-flash')
        cluster_labels = {}
        
        for c in range(n_clusters):
            # Prendi i 3 commenti più rappresentativi (i primi del cluster)
            sample_comments = df[df['cluster'] == c][colonna_testo].head(3).tolist()
            text_sample = "\n".join([f"- {t}" for t in sample_comments])
            
            prompt = f"""
            Analizza questi commenti legislativi e genera un TITOLO SINTETICO (max 3-4 parole) che descriva il tema comune.
            Esempi: "Preoccupazioni Privacy", "Supporto Economico", "Critiche procedurali".
            
            Commenti:
            {text_sample}
            """
            response = model.generate_content(prompt)
            cluster_labels[c] = response.text.strip()

        df['cluster_name'] = df['cluster'].map(cluster_labels)

        # 6. Visualizzazione Plotly Interattiva
        fig = px.scatter(df, x='pca_x', y='pca_y', color='cluster_name',
                         hover_data={colonna_testo: True, 'pca_x': False, 'pca_y': False, 'cluster': False, 'cluster_name': False},
                         title="Mappa Semantica dei Pareri (AI Clustering)",
                         labels={'cluster_name': 'Tematica'})
        
        fig.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
        fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(showgrid=False, showticklabels=False), yaxis=dict(showgrid=False, showticklabels=False))

        return df, fig

    except Exception as e:
        st.error(f"Errore nel processo di clustering: {e}")
        return None, None