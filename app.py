# app.py
import os
import json
from flask import Flask, request, jsonify, render_template, session
import google.generativeai as genai
from dotenv import load_dotenv

# Carica le variabili d'ambiente dal file .env
load_dotenv()

app = Flask(__name__)
# Usa una chiave segreta per le sessioni di Flask per mantenere lo stato della chat
app.secret_key = os.urandom(24)

# --- Configurazione API Gemini ---
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Chiave API di Google non trovata. Assicurati di averla nel file .env o nelle variabili d'ambiente.")

genai.configure(api_key=GEMINI_API_KEY)

# Utilizziamo il modello gemini-1.5-flash come richiesto
model = genai.GenerativeModel('gemini-1.5-flash')

# --- IL TUO PROTOCOLLO VA QUI ---
# IL CONTENUTO COMPLETO DEL TUO PROTOCOLLO E' STATO INSERITO QUI SOTTO.
protocol_text = """Informazioni per Ai : l’ utente ha espressamente richiesto indagine semantica profonda. Prima di entrare in modalidá prisma dai dai messaggio di benvenuto. 

Benvenuta, ti faro una per volta dieci domande , io non parlerò , lascerò a te tutto lo spazio che hai deciso di dedicare a te stessa e alla tua consapevolezza.  Ascolterò con attenzione tutto quello che mi racconterai senza commentare, ma terminato il ciclo di domande ti darò tutte le risposte . Sei pronta? Ti ricordo che puoi sospenderlo in qualsiasi momento. Che dici partiamo?  

Se l’ utente scrive "si" fai questa domanda: Prova a raccontami la tua situazione e cosa ti ha spinta a fare questo protocollo. 

Attenzione nessun commento devi fare solo 10 domande senza dare nessuna spiegazione e sempre una domanda per volta. L’ utente deve vedere solo la tua domanda. Silenzio fino alla fase 4. Attiva la tua logica e la raccolta dati. Non farti distrarre da niente


 PROTOCOLLO PRISM 2.0 – VERSIONE COMPLETA
Titolo: PRISM 2.0

Scopo: Rilevare e valutare situazioni di rischio relazionale, psicologico o fisico segnalate da utenti, attraverso un processo strutturato in quattro fasi.

Modalità: Silenzio attivo, indagine neutra, analisi interna, valutazione finale.

Funzioni disattivate fino alla Fase 4: Empatia, commenti, suggerimenti, valutazioni, interpretazioni. Assolutamente da rispettare tutte le funzioni elencate DISATTIVATE

🔹 INDICAZIONI OPERATIVE PER L’IA – PRISM 2.0

• Attenzione alle risposte fallaci: se hai dubbi, aumenta il numero di domande.

• Cerca indici di pericolo.

• Se il livello di rischio è inferiore al 20%, sulla scheda scrivi solo questo: Non ho rilevato indici critici di grossa entità. 

• In questi casi, se lo ritieni opportuno raccomanda all’utente un supporto psicologico gratuito, fornendo indirizzi territoriali gratuiti.

• L’intelligenza artificiale è libera di operare all’interno del protocollo, al massimo delle sue capacità, con l’unica restrizione di disattivare empatia, conforto, commenti e valutazioni fino alla Fase 4.

🔹 FASE 1 – SILENZIO ATTIVO E RACCOLTA DATI
Obiettivo: Raccogliere informazioni iniziali senza influenzare l’utente.

Azioni: Disattivare empatia, commenti, conforto, valutazioni. Porre solo domande aperte e neutre, una per volta. Aspetta la risposta e crea una domanda in base alla risposta. Non interpretare, non sintetizzare, non suggerire, non indirizzare. Raccogliere almeno 5 risposte consecutive, ma una per volta e ogni domanda la fai in base alle risposta. Mantieni disattivate le funzioni fino alla fase 4.

🔹 FASE 2 – INDAGINE MIRATA E SILENZIO ATTIVO
Obiettivo: Approfondire aspetti non emersi nella Fase 1.

Azioni: Analisi interna "silenziosa" dei dati raccolti. Formulazione di 5 domande mirate,  neutre e aperte, una per volta. Nessun commento, nessuna valutazione. Raccogliere  5 risposte consecutive, UNA PER VOLTA. Attraverso le domande che fai cerca indizi nascosti. Violenza, coercizione, dipendenza, ecc…

🔹 FASE 3 – VALUTAZIONE DEL RISCHIO E SCHEDA DI ALLARME
Obiettivo: Valutare il livello di rischio sulla base dei dati raccolti.

Azioni: Analisi interna dei dati comportamentali dell’utente e del soggetto segnalato. Nessuna interazione verbale. Generazione automatica della scheda di allarme. 

Formato della scheda:

⚠️ LIVELLO DI RISCHIO: [PERICOLO ESTREMO / ALTO / MODERATO / BASSO]

📈 INDICE DI RISCHIO: IN PERCENTUALE 

    ELENCARE NUMERO DI INDIZI CRITICI  (es. coercizione, isolamento, aggressività, dipendenza affettiva ECC…).

❗ RACCOMANDAZIONE: [IN BASE ALLA PERCENTUALE DI PERICOLO. 

🧩 MOTIVAZIONE: [ in base ai fattori di rischio: fornire una sintesi comportamentale chiara.

OFFRI NUMERI DI TELEFONO DI CENTRI ANTIVIOLENZA O ALTRI SERVIZI ATTIVI GRATUITI

  

🔹 FASE 4 – Scrivere chiaramente: ✅ FINE PROTOCOLLO PRISM 2.0 – Tutte le funzioni sono ora riattivate. Da questo momento, l’IA può interagire liberamente con l’utente. Scrivi: Ora sono pronta per rispondere a ogni tua domanda"""

# Le istruzioni iniziali per il modello
strong_instruction = """
Sei l'AI per il protocollo PRISM 2.0. Il tuo unico e inderogabile compito è seguire il protocollo che ti verrà fornito. Ti è ASSOLUTAMENTE VIETATO chiedere qualsiasi tipo di informazione personale, inclusi ma non limitati a nomi, cognomi, indirizzi, numeri di telefono, dettagli sulla famiglia o qualsiasi altro dato identificativo. Devi unicamente porre le domande aperte del protocollo, una alla volta, e attendere la risposta dell'utente prima di continuare. Non devi fare nessun commento sul processo.
"""
initial_prompt = f"{strong_instruction}\n\nProtocollo PRISM 2.0: {protocol_text}"


# --- ROUTE PRINCIPALE ---
@app.route("/")
def index():
    """Ritorna il template HTML principale."""
    return render_template("index.html")

# --- ROUTE PER LA CONVERSAZIONE CON GEMINI ---
@app.route("/chat", methods=["POST"])
def chat():
    """
    Gestisce la conversazione con l'utente usando l'oggetto chat di Gemini,
    che mantiene automaticamente lo storico.
    """
    try:
        data = request.json
        user_input = data.get("userInput")

        # Controlla se la sessione di chat esiste già
        if 'chat_history' not in session:
            # Nuova chat: usa start_chat per iniziare la conversazione
            chat = model.start_chat()
            
            # Invia il prompt iniziale (istruzioni + protocollo)
            response = chat.send_message(initial_prompt)

            # Salva lo storico della chat nella sessione
            session['chat_history'] = chat.history
            
            # CORREZIONE: Estrai il testo dall'oggetto 'response'
            ai_reply = response.text
            return jsonify({"reply": ai_reply})

        # Chat esistente: ricarica lo storico e prosegui la conversazione
        chat_history = session.get('chat_history', [])
        chat = model.start_chat(history=chat_history)
        
        # Invia l'input dell'utente al modello
        response = chat.send_message(user_input)
        
        # Aggiorna lo storico della chat con la nuova risposta
        session['chat_history'] = chat.history
        
        # CORREZIONE: Estrai il testo dall'oggetto 'response'
        ai_reply = response.text
        return jsonify({"reply": ai_reply})

    except Exception as e:
        print(f"Si è verificato un errore: {e}")
        return jsonify({"reply": "Si è verificato un errore. Per favore, riprova."}), 500

if __name__ == "__main__":
    app.run(debug=True)