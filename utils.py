import google.generativeai as genai
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from PyPDF2 import PdfReader

# --- CONFIGURAZIONE MODELLO GENERATIVO ---
MODEL_TEXT = "gemini-3-flash"

def get_available_embedding_model():
    """Trova dinamicamente il miglior modello di embedding disponibile nell'account"""
    try:
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                return m.name # Restituisce es. 'models/text-embedding-004'
    except:
        return "models/text-embedding-004" # Fallback standard
    return "models/text-embedding-004"

def esegui_clustering_opinioni(df, colonna_testo='Parere'):
    """
    Esegue il clustering risolvendo i problemi di 404 e dati insufficienti.
    """
    # 1. Controllo rigoroso dei dati
    if df is None or df.empty:
        st.warning("⚠️ Il database è vuoto. Inserisci dei pareri per vedere l'analisi.")
        return None, None
        
    n_campioni = len(df)
    if n_campioni < 3:
        st.warning(f"📊 Dati insufficienti: hai inserito {n_campioni} pareri, ma ne servono almeno 3 per creare dei gruppi.")
        return None, None

    try:
        # 2. Identificazione modello
        embedding_model_name = get_available_embedding_model()
        
        @st.cache_data(show_spinner=False)
        def get_embeddings_safe(texts):
            # Esegue l'embedding in batch per essere più veloce e stabile
            result = genai.embed_content(
                model=embedding_model_name,
                content=texts,
                task_type="clustering"
            )
            return result['embeddings']

        with st.spinner("🤖 L'intelligenza artificiale sta analizzando le sfumature dei pareri..."):
            # 3. Generazione Embeddings
            list_testi = df[colonna_testo].astype(str).tolist()
            vectors = get_embeddings_safe(list_testi)
            matrix = np.array(vectors)

            # 4. Clustering (K-Means)
            # Adattiamo il numero di cluster: se hai pochi dati, ne facciamo solo 2
            n_clusters = 3 if n_campioni >= 5 else 2
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(matrix)

            # 5. Riduzione PCA per grafico 2D
            pca = PCA(n_components=2)
            coords = pca.fit_transform(matrix)
            df['x'] = coords[:, 0]
            df['y'] = coords[:, 1]

            # 6. Auto-Labeling con Gemini 3 Flash
            model = genai.GenerativeModel(MODEL_TEXT)
            labels = {}
            for i in range(n_clusters):
                cluster_samples = df[df['cluster'] == i][colonna_testo].head(2).tolist()
                prompt = f"Riassumi il tema comune di questi commenti legislativi in 3 parole: {cluster_samples}"
                try:
                    res = model.generate_content(prompt)
                    labels[i] = res.text.strip().replace('"', '')
                except:
                    labels[i] = f"Argomento {i+1}"
            
            df['cluster_name'] = df['cluster'].map(labels)

            # 7. Creazione Grafico Interattivo
            fig = px.scatter(
                df, x='x', y='y', 
                color='cluster_name',
                hover_data={colonna_testo: True, 'x': False, 'y': False},
                title="Mappa Semantica delle Opinioni dei Cittadini",
                labels={'cluster_name': 'Tematica rilevata'},
                template="plotly_white"
            )
            
            fig.update_traces(marker=dict(size=15, line=dict(width=1.5, color='white')))
            fig.update_layout(xaxis_visible=False, yaxis_visible=False) # Pulizia assi

            return df, fig

    except Exception as e:
        st.error(f"❌ Errore tecnico nel clustering: {str(e)}")
        # Log dettagliato per debug in console
        print(f"DEBUG ERROR: {e}")
        return None, None

# --- ALTRE FUNZIONI (PDF e CV) ---
def analizza_testo_pdf(file):
    reader = PdfReader(file)
    return "".join([p.extract_text() for p in reader.pages])

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel(MODEL_TEXT)
    prompt = f"Estrai Area (Tecnologia, Diritto, Ambiente, Economia) e profilo (15 parole) da questo CV: {testo_cv[:2000]}"
    try:
        response = model.generate_content(prompt)
        return "Area", response.text
    except:
        return None, None