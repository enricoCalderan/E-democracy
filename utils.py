from PyPDF2 import PdfReader
import google.generativeai as genai
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

# --- CONFIGURAZIONE MODELLI 2026 ---
# Utilizziamo Gemini 3 Flash per la generazione e l'ultima versione embedding
MODEL_TEXT = "gemini-3-flash" 
MODEL_EMBEDDING = "text-embedding-004" 

def analizza_testo_pdf(file):
    reader = PdfReader(file)
    testo = "".join([page.extract_text() for page in reader.pages])
    return testo

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel(MODEL_TEXT)
    prompt = f"Analizza questo CV (Area: Tecnologia, Diritto, Ambiente, Economia) e fanne una descrizione formale di 15 parole: {testo_cv[:3000]}"
    try:
        response = model.generate_content(prompt)
        # Logica di parsing semplificata per brevità
        return "Area Rilevata", response.text
    except Exception as e:
        return None, None

def esegui_clustering_opinioni(df, colonna_testo='Parere'):
    """
    Esegue clustering semantico con gestione robusta degli errori 404.
    """
    # 1. Controllo Dati (Soglia minima per senso matematico)
    if df is None or len(df) < 3:
        st.warning("📊 Dati insufficienti: servono almeno 3 pareri per creare dei gruppi significativi.")
        return None, None

    try:
        # 2. Funzione di Embedding con Fallback
        def get_embedding(text):
            if not isinstance(text, str) or not text.strip():
                return np.zeros(768)
            
            # Proviamo a usare il modello più recente, se fallisce usiamo il legacy
            try:
                result = genai.embed_content(
                    model=f"models/{MODEL_EMBEDDING}",
                    content=text,
                    task_type="clustering"
                )
            except:
                # Fallback per compatibilità v1beta/v1
                result = genai.embed_content(
                    model="models/embedding-001", 
                    content=text,
                    task_type="clustering"
                )
            return result['embedding']

        with st.spinner("L'intelligenza artificiale sta raggruppando i pareri simili..."):
            # Trasformazione in vettori
            embeddings = [get_embedding(t) for t in df[colonna_testo].tolist()]
            matrix = np.array(embeddings)

            # 3. Clustering (K-Means)
            # Numero di cluster dinamico: mai superiore al numero di commenti
            n_clusters = min(3, len(df))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(matrix)

            # 4. Riduzione Dimensionale (PCA)
            pca = PCA(n_components=2)
            components = pca.fit_transform(matrix)
            df['pca_x'] = components[:, 0]
            df['pca_y'] = components[:, 1]

            # 5. Auto-Labeling con Gemini 3 Flash
            model = genai.GenerativeModel(MODEL_TEXT)
            labels = {}
            for i in range(n_clusters):
                campioni = df[df['cluster'] == i][colonna_testo].head(2).tolist()
                prompt = f"Riassumi in 3 parole il tema di questi commenti: {campioni}"
                try:
                    res = model.generate_content(prompt)
                    labels[i] = res.text.strip().replace('"', '')
                except:
                    labels[i] = f"Tema {i+1}"

            df['cluster_name'] = df['cluster'].map(labels)

            # 6. Grafico Plotly
            fig = px.scatter(
                df, x='pca_x', y='pca_y', 
                color='cluster_name',
                hover_data=[colonna_testo],
                title="Mappa Semantica delle Opinioni",
                labels={'cluster_name': 'Argomento'},
                template="plotly_white"
            )
            fig.update_traces(marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey')))
            
            return df, fig

    except Exception as e:
        st.error(f"Errore tecnico nel clustering: {e}")
        return None, None