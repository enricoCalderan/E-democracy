import google.generativeai as genai
import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from PyPDF2 import PdfReader

# --- CONFIGURAZIONE MODELLO GENERATIVO ---
MODEL_TEXT = "gemini-2.5-flash"

def analizza_testo_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def analizza_cv_con_gemini(testo_cv):
    model = genai.GenerativeModel(MODEL_TEXT)
    
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
    

def get_available_embedding_model():
    """Trova dinamicamente il miglior modello di embedding disponibile nell'account"""
    try:
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                return m.name # Restituisce es. 'models/text-embedding-004'
    except:
        return "models/text-embedding-004" # Fallback standard
    return "models/text-embedding-004"

def get_available_embedding_model():
    """Trova il modello di embedding corretto per evitare l'errore 404"""
    try:
        for m in genai.list_models():
            if 'embedContent' in m.supported_generation_methods:
                return m.name
    except:
        return "models/text-embedding-004"
    return "models/text-embedding-004"

def esegui_clustering_opinioni(df, colonna_testo='Parere'):
    if df is None or df.empty or len(df) < 3:
        st.warning("Servono almeno 3 pareri per attivare il clustering AI.")
        return None, None

    try:
        model_name = get_available_embedding_model()
        list_testi = df[colonna_testo].astype(str).tolist()

        with st.spinner("L'IA sta organizzando i pareri per temi..."):
            # 1. GENERAZIONE EMBEDDINGS
            response = genai.embed_content(
                model=model_name,
                content=list_testi,
                task_type="clustering"
            )

            # Estrazione sicura dei vettori
            vectors = response.get('embeddings') or response.get('embedding')
            if vectors is None:
                st.error("L'API non ha restituito vettori validi.")
                return None, None
            
            matrix = np.array(vectors)

            # 2. CLUSTERING K-MEANS
            n_clusters = 3 if len(df) >= 5 else 2
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            df['cluster'] = kmeans.fit_predict(matrix)

            # 3. RIDUZIONE PCA (Da 768D a 2D per il grafico)
            pca = PCA(n_components=2)
            coords = pca.fit_transform(matrix)
            df['x'] = coords[:, 0]
            df['y'] = coords[:, 1]

            # 4. AUTO-LABELING BATCH (Una sola chiamata per tutti i cluster)
            model = genai.GenerativeModel(MODEL_TEXT)
            
            # Prepariamo un unico prompt per tutti i gruppi
            prompt_batch = "Analizza questi gruppi di commenti e per ognuno scrivi un titolo di MAX 3 PAROLE.\n"
            for i in range(n_clusters):
                campioni = df[df['cluster'] == i][colonna_testo].head(3).tolist()
                prompt_batch += f"\nGRUPPO {i}: {campioni}"
            prompt_batch += "\n\nRispondi solo con l'elenco dei titoli, uno per riga."

            labels = {}
            try:
                res = model.generate_content(prompt_batch)
                # Pulizia della risposta: prendiamo le righe e tagliamo a 3 parole
                righe = [r.replace("- ", "").strip() for r in res.text.strip().split("\n") if r.strip()]
                for i in range(n_clusters):
                    if i < len(righe):
                        labels[i] = " ".join(righe[i].split()[:3]).replace("*", "")
                    else:
                        labels[i] = f"Tema {i+1}"
            except:
                for i in range(n_clusters): labels[i] = f"Area Tematica {i+1}"

            df['cluster_name'] = df['cluster'].map(labels)
            
            # 5. GRAFICO PLOTLY
            fig = px.scatter(
                df, x='x', y='y', color='cluster_name',
                hover_data={colonna_testo: True, 'x': False, 'y': False, 'cluster_name': False},
                title="Mappa Semantica delle Opinioni",
                template="plotly_white",
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig.update_traces(marker=dict(size=14, line=dict(width=1, color='white')))
            fig.update_layout(xaxis_visible=False, yaxis_visible=False)

            return df, fig

    except Exception as e:
        st.error(f"Errore tecnico nel clustering: {str(e)}")
        return None, None