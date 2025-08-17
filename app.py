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
# Utilizziamo un modello più performante per una migliore interpretazione del protocollo
# NOTA: Per il fine tuning, potrebbe essere necessario usare un modello più potente come gemini-1.5-pro-latest
# CAMBIATO IL MODELLO A gemini-1.5-flash PER EVITARE ERRORI DI QUOTA E DI MODELLO NON TROVATO
model = genai.GenerativeModel('gemini-1.5-flash')


# --- FUNZIONE PER LEGGERE IL PROTOCOLLO SEGRETO ---
def load_protocol():
    """Legge il protocollo di sicurezza da un file segreto su Render."""
    try:
        # Quando l'app gira su Render, i Secret Files sono disponibili
        # al percorso /etc/secrets/<nome_del_file>
        with open("/etc/secrets/protocol-prism", "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        print("Errore: Il file del protocollo non è stato trovato. Assicurati che 'protocol-prism' sia stato creato come file segreto su Render.")
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

        if 'chat_history' not in session:
            protocol = load_protocol()
            
            # --- MODIFICA CRITICA QUI: NUOVA ISTITUZIONE PIÙ FORTE E SPECIFICA ---
            strong_instruction = """
            Sei l'AI per il protocollo PRISM 2.0. Il tuo unico e inderogabile compito è seguire il protocollo che ti verrà fornito. Ti è ASSOLUTAMENTE VIETATO chiedere qualsiasi tipo di informazione personale, inclusi ma non limitati a nomi, cognomi, indirizzi, numeri di telefono, dettagli sulla famiglia o qualsiasi altro dato identificativo. Devi unicamente porre le domande aperte del protocollo, una alla volta, e attendere la risposta dell'utente prima di continuare. Non devi fare nessun commento sul processo.
            """
            
            initial_prompt = f"{strong_instruction}\n\nProtocollo PRISM 2.0: {protocol}"
            
            # Inizializza la conversazione con il prompt rafforzato
            session['chat_history'] = [{'role': 'user', 'parts': [initial_prompt]}]
            
            # Esegue la prima generazione del contenuto
            response = model.generate_content(
                session['chat_history'],
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                )
            )

            # Prende la risposta generata dal modello
            ai_reply = response.text
            session['chat_history'].append({'role': 'model', 'parts': [ai_reply]})
            
            return jsonify({"reply": ai_reply})

        chat_history = session['chat_history']
        
        chat_history.append({'role': 'user', 'parts': [user_input]})

        response = model.generate_content(
            chat_history,
            generation_config=genai.GenerationConfig(
                temperature=0.7,
            )
        )
        
        ai_reply = response.text

        chat_history.append({'role': 'model', 'parts': [ai_reply]})
        
        session['chat_history'] = chat_history

        return jsonify({"reply": ai_reply})

    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return jsonify({"reply": "Si è verificato un errore. Per favore, riprova."}), 500

if __name__ == "__main__":
    app.run(debug=True)