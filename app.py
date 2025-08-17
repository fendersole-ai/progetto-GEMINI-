import os
import requests
from flask import Flask, request, jsonify, render_template

# Funzione per caricare il protocollo dal file segreto
def load_protocol_from_secret_file():
    """Legge il protocollo di sicurezza da un file segreto su Render."""
    try:
        # Quando l'app gira su Render, i Secret Files sono disponibili
        # al percorso /etc/secrets/<nome_del_file>
        with open("/etc/secrets/protocol-prism", "r", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        print(f"Errore nel caricare il protocollo dal file segreto: {e}")
        return "Non è stato possibile caricare il protocollo. Controlla le impostazioni del tuo file segreto su Render."

app = Flask(__name__)

# Configura l'API key per Gemini
api_key = os.environ.get("GOOGLE_API_KEY")

if api_key is None:
    print("Errore: la variabile d'ambiente GOOGLE_API_KEY non è stata trovata.")
    # Puoi decidere come gestire l'errore, ad esempio terminando l'app o mostrando un messaggio
    exit(1)

# L'URL dell'API di Google Gemini
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    user_message = data.get("message")
    
    # Carica il protocollo segreto
    protocol_text = load_protocol_from_secret_file()
    
    if "Non è stato possibile caricare" in protocol_text:
        return jsonify({"response": "Errore: " + protocol_text})

    # Invia il messaggio dell'utente insieme al protocollo
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": protocol_text},
                    {"text": user_message}
                ]
            }
        ]
    }
    
    response = requests.post(API_URL, json=payload)
    
    if response.status_code == 200:
        gemini_response = response.json()
        if 'candidates' in gemini_response:
            return jsonify({"response": gemini_response['candidates'][0]['content']['parts'][0]['text']})
        else:
            return jsonify({"response": "La risposta di Gemini non ha il formato atteso."})
    else:
        print(f"Errore dell'API: {response.text}")
        return jsonify({"response": "Si è verificato un errore con l'API di Gemini."}), response.status_code

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

