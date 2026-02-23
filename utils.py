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
    if df is None or df.empty or len(df) < 3:
        st.warning("Servono almeno 3 pareri per attivare il clustering AI.")
        return None, None

    try:
        model_name = get_available_embedding_model()
        list_testi = df[colonna_testo].astype(str).tolist()

        with st.spinner("Analisi semantica in corso..."):
            # Chiamata API
            response = genai.embed_content(
                model=model_name,
                content=list_testi,
                task_type="clustering"
            )

            # --- FIX ERRORE 'embeddings' ---
            # Verifichiamo quale chiave ha usato l'API (singolare o plurale)
            if 'embeddings' in response:
                vectors = response['embeddings']
            elif 'embedding' in response:
                vectors = response['embedding']
            else:
                # Debug estremo se non troviamo nessuna delle due
                st.error(f"Struttura API imprevista. Chiavi ricevute: {response.keys()}")
                return None, None
            
            matrix = np.array(vectors)

            # 3. Clustering K-Means
            n_clusters = 3 if len(df) >= 5 else 2
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(matrix)

            # 4. Riduzione PCA per grafico
            pca = PCA(n_components=2)
            coords = pca.fit_transform(matrix)
            df['x'] = coords[:, 0]
            df['y'] = coords[:, 1]

            # 5. Auto-Labeling con Gemini (VERSIONE BATCH - Una sola chiamata)
            model = genai.GenerativeModel(MODEL_TEXT)
            
            # Prepariamo un unico grande prompt con tutti i gruppi
            prompt_full = "Analizza questi gruppi di pareri legislativi e per ogni gruppo genera un'etichetta di MASSIMO 3 PAROLE.\n"
            for i in range(n_clusters):
                campioni = df[df['cluster'] == i][colonna_testo].head(2).tolist()
                prompt_full += f"\nGRUPPO {i}: {campioni}"
            
            prompt_full += "\n\nRispondi ESCLUSIVAMENTE con un elenco puntato, esempio: \n- Titolo 1\n- Titolo 2"

            labels = {}
            try:
                # Facciamo un'unica chiamata per risparmiare tempo e quote API
                res = model.generate_content(prompt_full)
                # Puliamo la risposta e dividiamola in righe
                linee = [line.replace("- ", "").strip() for line in res.text.strip().split("\n") if line.strip()]
                
                for i in range(n_clusters):
                    if i < len(linee):
                        # Taglio forzato alle prime 3 parole per sicurezza
                        titolo_pulito = " ".join(linee[i].split()[:3])
                        labels[i] = titolo_pulito
                    else:
                        labels[i] = f"Tema {i+1}"
            except Exception as e:
                st.error(f"Errore etichettatura AI: {e}")
                # Fallback se la chiamata unica fallisce
                for i in range(n_clusters):
                    labels[i] = f"Area {i+1}"

            df['cluster_name'] = df['cluster'].map(labels)

            # 6. Grafico Plotly
            fig = px.scatter(
                df, x='x', y='y', color='cluster_name',
                hover_data={colonna_testo: True, 'x': False, 'y': False},
                title="Mappa delle Opinioni (Clustering Semantico)",
                template="plotly_white"
            )
            fig.update_traces(marker=dict(size=14, line=dict(width=1, color='white')))
            fig.update_layout(xaxis_visible=False, yaxis_visible=False)

            return df, fig

    except Exception as e:
        st.error(f"Errore tecnico nel clustering: {str(e)}")
        return None, None