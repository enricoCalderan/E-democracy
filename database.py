import pandas as pd
import os

def get_utente_db(nome, cognome):
    if not os.path.exists("database_utenti.csv"):
        return None
    try:
        df = pd.read_csv("database_utenti.csv")
        utente = df[(df['Nome'].str.lower() == nome.lower()) & 
                    (df['Cognome'].str.lower() == cognome.lower())]
        if not utente.empty:
            return utente.iloc[0]
        return None
    except Exception:
        return None

def salva_nuovo_utente(nome, cognome, area, password, eta, via, citta, descrizione):
    nuovo_utente = pd.DataFrame([[nome, cognome, area, eta, via, citta, descrizione, password]], 
                                columns=["Nome", "Cognome", "Area", "Eta", "Indirizzo", "Citta", "Descrizione", "Password"])
    if not os.path.exists("database_utenti.csv"):
        nuovo_utente.to_csv("database_utenti.csv", index=False)
    else:
        nuovo_utente.to_csv("database_utenti.csv", mode='a', header=False, index=False)

def get_parlamentare_db(nome, cognome):
    if not os.path.exists("database_parlamentari.csv"):
        return None
    try:
        df = pd.read_csv("database_parlamentari.csv")
        parlamentare = df[(df['Nome'].str.lower() == nome.lower()) & 
                          (df['Cognome'].str.lower() == cognome.lower())]
        if not parlamentare.empty:
            return parlamentare.iloc[0]
        return None
    except Exception:
        return None

def salva_parere(legge, testo, area, posizione, autore, giudizio):
    if os.path.exists("database_pareri.csv"):
        df = pd.read_csv("database_pareri.csv", on_bad_lines='skip')
        if 'Posizione' not in df.columns: df['Posizione'] = "Non specificato"
        if 'Autore' not in df.columns: df['Autore'] = "Anonimo"
        if 'Giudizio' not in df.columns: df['Giudizio'] = "Non specificato"
        
        # Rimuove eventuale parere precedente
        df = df[~((df['Legge'] == legge) & (df['Autore'] == autore))]
    else:
        df = pd.DataFrame(columns=["Legge", "Parere", "Area", "Posizione", "Autore", "Giudizio"])

    nuovo_parere = pd.DataFrame([[legge, testo, area, posizione, autore, giudizio]], columns=["Legge", "Parere", "Area", "Posizione", "Autore", "Giudizio"])
    df_aggiornato = pd.concat([df, nuovo_parere], ignore_index=True)
    df_aggiornato.to_csv("database_pareri.csv", index=False)

def get_tutti_pareri():
    if os.path.exists("database_pareri.csv"):
        return pd.read_csv("database_pareri.csv", on_bad_lines='skip')
    return pd.DataFrame()

def get_voto_utente(votante, autore_parere, legge):
    if not os.path.exists("database_voti.csv"):
        return 0
    try:
        df = pd.read_csv("database_voti.csv")
        voto = df[(df['Votante'] == votante) & 
                  (df['AutoreParere'] == autore_parere) & 
                  (df['Legge'] == legge)]
        if not voto.empty:
            return int(voto.iloc[0]['Voto'])
    except:
        pass
    return 0

def salva_voto(votante, autore_parere, legge, voto):
    file_path = "database_voti.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        
        # Cerca se esiste già un voto
        filtro = (df['Votante'] == votante) & (df['AutoreParere'] == autore_parere) & (df['Legge'] == legge)
        voto_esistente = df[filtro]
        
        # Rimuovi sempre il voto precedente (per aggiornarlo o eliminarlo)
        df = df[~filtro]
        
        # Se il voto era identico a quello nuovo, significa che l'utente vuole annullarlo (toggle)
        if not voto_esistente.empty and int(voto_esistente.iloc[0]['Voto']) == voto:
            df.to_csv(file_path, index=False)
            return # Esce senza aggiungere il nuovo voto
    else:
        df = pd.DataFrame(columns=["Votante", "AutoreParere", "Legge", "Voto"])
    
    nuovo_voto = pd.DataFrame([[votante, autore_parere, legge, voto]], 
                              columns=["Votante", "AutoreParere", "Legge", "Voto"])
    df = pd.concat([df, nuovo_voto], ignore_index=True)
    df.to_csv(file_path, index=False)

def get_punteggio_parere(autore_parere, legge):
    if not os.path.exists("database_voti.csv"):
        return 0
    try:
        df = pd.read_csv("database_voti.csv")
        voti = df[(df['AutoreParere'] == autore_parere) & (df['Legge'] == legge)]
        return int(voti['Voto'].sum())
    except:
        return 0

def get_commenti_parere(autore_parere, legge):
    if not os.path.exists("database_commenti.csv"):
        return pd.DataFrame()
    try:
        df = pd.read_csv("database_commenti.csv")
        return df[(df['AutoreParere'] == autore_parere) & (df['Legge'] == legge)]
    except:
        return pd.DataFrame()

def salva_commento(autore_commento, autore_parere, legge, testo):
    file_path = "database_commenti.csv"
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # Rimuovi commento precedente dello stesso autore su questo parere (per permettere la modifica)
        df = df[~((df['AutoreCommento'] == autore_commento) & 
                  (df['AutoreParere'] == autore_parere) & 
                  (df['Legge'] == legge))]
    else:
        df = pd.DataFrame(columns=["AutoreCommento", "AutoreParere", "Legge", "Testo"])
    
    nuovo = pd.DataFrame([[autore_commento, autore_parere, legge, testo]], 
                         columns=["AutoreCommento", "AutoreParere", "Legge", "Testo"])
    df = pd.concat([df, nuovo], ignore_index=True)
    df.to_csv(file_path, index=False)

def get_proposte_legge():
    if os.path.exists("database_proposte.csv"):
        try:
            df = pd.read_csv("database_proposte.csv")
            return df.to_dict('records')
        except Exception:
            return []
    return []