from PyPDF2 import PdfReader
import google.generativeai as genai
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# --- CONFIGURAZIONE MODELLI ---
# Utilizziamo modelli standard e supportati nel 2026
MODEL_TEXT = "gemini-1.5-flash" 
MODEL_EMBEDDING = "models/text-embedding-004" # Modello aggiornato e stabile

def analizza_testo_pdf(file):
    reader = PdfReader(file)
    testo = "".join([page.extract_text() for page in reader.pages])
    return testo

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel(MODEL_TEXT)
    
    prompt = f"""
    Agisci come un Senior HR Consultant esperto in analisi tecnica. 
    Analizza il seguente CV con un approccio analitico e formale.
    
    1. Identifica l'area di competenza principale esclusivamente tra: Tecnologia, Diritto, Ambiente, Economia.
       Se il profilo è generico o in fase di formazione senza una specializzazione chiara, scrivi 'Nessuna'.
       
    2. Redigi un profilo professionale sintetico in terza persona (max 15 parole). 
    Focalizzati esclusivamente su qualifica, seniority e competenze core senza nomi propri.
    
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
    model = genai.GenerativeModel(MODEL_TEXT)
    testo_dati = ""
    for p in lista_pareri:
        testo_dati += f"- [Punteggio: {p['Punteggio']}] Posizione: {p['Posizione']} | Contenuto: {p['Testo']}\n"

    prompt = f"Analizza questi pareri per la legge {titolo_legge} e crea un report tecnico: {testo_dati}"
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Errore durante la generazione del report: {e}"

def esegui_clustering_opinioni(df, colonna_testo='Parere'):
    """
    Esegue clustering semantico. Risolve l'errore 404 e gestisce pochi dati.
    """
    # 1. Controllo Dati (Minimo 3 per un clustering sensato)
    if df is None or len(df) < 3:
        st.warning("Dati insufficienti per generare i cluster (minimo 3 pareri richiesti).")
        return None, None

    try:
        # 2. Generazione Embeddings (Modello corretto: text-embedding-004)
        def get_embedding(text):
            if not isinstance(text, str) or not text.strip():
                return np.zeros(768)
            
            result = genai.embed_content(
                model=MODEL_EMBEDDING,
                content=text,
                task_type="clustering"
            )
            return result['embedding']

        with st.spinner("Generazione mappa semantica in corso..."):
            embeddings = df[colonna_testo].apply(get_embedding).tolist()
            matrix = np.array(embeddings)

            # 3. Clustering (K-Means)
            # Evitiamo di chiedere più cluster di quanti siano i pareri
            n_clusters = min(3, len(df)) 
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(matrix)

            # 4. Riduzione Dimensionale (PCA)
            pca = PCA(n_components=2)
            components = pca.fit_transform(matrix)
            df['pca_x'] = components[:, 0]
            df['pca_y'] = components[:, 1]

            # 5. Auto-Labeling con Gemini
            model = genai.GenerativeModel(MODEL_TEXT)
            cluster_labels = {}
            
            for c in range(n_clusters):
                sample_comments = df[df['cluster'] == c][colonna_testo].head(3).tolist()
                text_sample = "\n".join([f"- {t}" for t in sample_comments])
                
                prompt = f"Genera un titolo di 3 parole per questo gruppo di commenti: {text_sample}"
                response = model.generate_content(prompt)
                cluster_labels[c] = response.text.strip().replace('"', '')

            df['cluster_name'] = df['cluster'].map(cluster_labels)

            # 6. Visualizzazione Plotly
            fig = px.scatter(df, x='pca_x', y='pca_y', color='cluster_name',
                             hover_data={colonna_testo: True, 'pca_x': False, 'pca_y': False, 'cluster_name': False},
                             title="Mappa Semantica dei Pareri",
                             template="plotly_white")
            
            fig.update_traces(marker=dict(size=14, line=dict(width=1, color='white')))
            
            return df, fig

    except Exception as e:
        st.error(f"Errore nel processo di clustering: {e}")
        return None, None