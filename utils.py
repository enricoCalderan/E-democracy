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

            # 5. Auto-Labeling con Gemini (Versione Potenziata)
            model = genai.GenerativeModel(MODEL_TEXT)
            labels = {}
            
            for i in range(n_clusters):
                # Prendiamo i 3 commenti più significativi di questo gruppo
                campioni = df[df['cluster'] == i][colonna_testo].head(3).tolist()
                
                # Creiamo un prompt molto più "imperativo"
                prompt_label = f"""
                Analizza questi pareri legislativi e scrivi un titolo di massimo 3 parole 
                che ne riassuma il contenuto comune. 
                NON scrivere 'Titolo:', scrivi SOLO le 3 parole.
                
                Esempi: 'Costi Manutenzione Strade', 'Dubbi Efficacia Tecnica', 'Privacy Dati Utenti'.
                
                Commenti da analizzare:
                {campioni}
                """
                
                try:
                    # Chiamata a Gemini
                    res = model.generate_content(prompt_label)
                    titolo = res.text.strip().replace('"', '').replace('*', '')
                    
                    # Se Gemini risponde vuoto o troppo lungo, usiamo un mini-riassunto
                    if len(titolo) > 50 or not titolo:
                        labels[i] = f"Tema {i+1}: " + campioni[0][:20] + "..."
                    else:
                        labels[i] = titolo
                except Exception as e:
                    # Se l'API fallisce ancora, usiamo il primo pezzo del primo commento come titolo
                    print(f"Errore etichetta cluster {i}: {e}")
                    labels[i] = f"Gruppo: {campioni[0][:25]}..."

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