import google.generativeai as genai

# --- CONFIGURAZIONE GEMINI ---
# Sostituisci 'IL_TUO_API_KEY' con la chiave reale
genai.configure(api_key="AIzaSyCIQZioZS3oCzgSauz7bhwNi3Wr16hahIM")

# --- DATI SIMULATI PROPOSTE DI LEGGE ---
PROPOSTE_LEGGE = [
    {"id": 1, "titolo": "Riforma del Codice della Strada", "area": "Diritto", "desc": "Inasprimento pene per guida al cellulare."},
    {"id": 2, "titolo": "DL 123 - Riforma Digitale PA", "area": "Tecnologia", "desc": "Incentivi per l'adozione dell'AI nella Pubblica Amministrazione."},
    {"id": 3, "titolo": "Tutela Aree Marine Protette", "area": "Ambiente", "desc": "Estensione dei vincoli per la pesca a strascico."},
    {"id": 4, "titolo": "Flat Tax Incrementale", "area": "Economia", "desc": "Nuove aliquote per le partite IVA."},
    {"id": 5, "titolo": "Regolamentazione Droni Urbani", "area": "Tecnologia", "desc": "Norme di sicurezza per il volo in città."}
]