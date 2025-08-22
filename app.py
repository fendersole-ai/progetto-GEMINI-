# app.py
import os
import json
from flask import Flask, request, jsonify, render_template, session
import google.generativeai as genai
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
# Usa una chiave segreta per le sessioni di Flask
app.secret_key = os.urandom(24)

# --- Configurazione API Gemini ---
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Chiave API di Google non trovata. Assicurati di averla nel file .env o nelle variabili d'ambiente.")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


# --- FUNZIONE PER LEGGERE IL PROTOCOLLO SEGRETO ---
def load_protocol():
    """
    Legge il protocollo di sicurezza da un file.
    Cerca il file in locale o nel percorso dei segreti di Render.
    """
    # Controlla se l'app è in esecuzione su Render
    if os.environ.get('RENDER'):
        # Percorso per i Secret Files su Render
        protocol_path = "/etc/secrets/protocol-prism"
    else:
        # Percorso per l'ambiente locale
        protocol_path = "prism_protocol.txt"

    try:
        with open(protocol_path, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Errore: Il file del protocollo non è stato trovato al percorso: {protocol_path}")
        return ""

# --- ROUTE PRINCIPALE ---
@app.route("/")
def index():
    """Ritorna il template HTML principale."""
    return render_template("index.html")

# --- ROUTE PER LA CONVERSAZIONE CON GEMINI ---
@app.route("/chat", methods=["POST"])
def chat():
    """
    Gestisce la conversazione con l'utente.
    Invia i messaggi a Gemini, tenendo traccia dello storico della conversazione.
    """
    try:
        data = request.json
        user_input = data.get("userInput")

        # Istruzione forte per il modello (rimane la stessa)
        strong_instruction = """
        Sei l'AI per il protocollo PRISM 2.0. Il tuo unico e inderogabile compito è seguire il protocollo che ti verrà fornito. Ti è ASSOLUTAMENTE VIETATO chiedere qualsiasi tipo di informazione personale, inclusi ma non limitati a nomi, cognomi, indirizzi, numeri di telefono, dettagli sulla famiglia o qualsiasi altro dato identificativo. Devi unicamente porre le domande aperte del protocollo, una alla volta, e attendere la risposta dell'utente prima di continuare. Non devi fare nessun commento sul processo.
        """
        
        protocol = load_protocol()
        if not protocol:
            return jsonify({"reply": "Si è verificato un errore: il protocollo di sicurezza non è stato caricato correttamente."}), 500

        # Se la sessione non esiste, la inizializziamo con il prompt iniziale e le istruzioni
        if 'chat_history' not in session:
            # Creiamo il prompt iniziale con istruzioni e protocollo
            initial_prompt = f"{strong_instruction}\n\nProtocollo PRISM 2.0: {protocol}"
            session['chat_history'] = [{'role': 'user', 'parts': [initial_prompt]}]
            
            # Eseguiamo la prima generazione del contenuto
            response = model.generate_content(
                session['chat_history'],
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )

            # Prendiamo la risposta generata dal modello
            ai_reply = response.text
            session['chat_history'].append({'role': 'model', 'parts': [ai_reply]})
            
            return jsonify({"reply": ai_reply})

        # --- MODIFICA CRITICA QUI ---
        # A ogni turno, prepariamo il prompt includendo sempre l'istruzione e il protocollo
        # Questo garantisce che il modello non "dimentichi" il suo compito
        
        # Recuperiamo la cronologia della sessione
        chat_history = session['chat_history']
        
        # Creiamo un prompt combinato per il turno corrente
        # Includiamo istruzioni, protocollo e la nuova domanda dell'utente
        combined_prompt = f"{strong_instruction}\n\nProtocollo PRISM 2.0: {protocol}\n\nUtente: {user_input}"
        
        # Aggiungiamo il prompt combinato alla cronologia per il modello
        # Nota: invece di aggiungere solo user_input, aggiungiamo combined_prompt
        chat_history.append({'role': 'user', 'parts': [combined_prompt]})

        # Chiamiamo il modello con la cronologia aggiornata
        response = model.generate_content(
            chat_history,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
            )
        )
        
        ai_reply = response.text

        # Aggiungiamo solo la risposta del modello alla cronologia
        chat_history.append({'role': 'model', 'parts': [ai_reply]})
        
        session['chat_history'] = chat_history

        return jsonify({"reply": ai_reply})

    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return jsonify({"reply": "Si è verificato un errore. Per favore, riprova."}), 500

if __name__ == "__main__":
    app.run(debug=True)