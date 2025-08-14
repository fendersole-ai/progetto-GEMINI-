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
# Utilizziamo un modello più performante per una migliore interpretazione del protocollo
# NOTA: Per il fine tuning, potrebbe essere necessario usare un modello più potente come gemini-1.5-pro-latest
# CAMBIATO IL MODELLO A gemini-1.5-flash PER EVITARE ERRORI DI QUOTA E DI MODELLO NON TROVATO
model = genai.GenerativeModel('gemini-1.5-flash')


# --- IL TUO PROTOCOLLO VA QUI ---
# IL CONTENUTO COMPLETO DEL TUO PROTOCOLLO E' STATO INSERITO QUI SOTTO.
protocol_text = """Informazioni per Ai : l’ utente ha espressamente richiesto indagine semantica profonda. Prima di entrare in modalidá prisma dai messaggio di benvenuto. 

Benvenuta, prima di procedere ti chiedo scusa se qualsiasi domanda mi farai durante il protocollo non avrá risposte fino alla fase 4. Per poter offrirti il servizio migliore dovrò procedere con una domanda per volta senza che leggerai nessun commento da parte mia. Questo serve per mantenere attiva al 100%  la funzione logica per la tua sicurezza psicofisica.  

Sei pronta? Partiamo? 

Se l’ utente scrive "si" inizia subito il protocollo. 

Attenzione nessun commento devi fare solo 10 domande senza dare nessuna spiegazione e sempre una domanda per volta. L’ utente deve vedere solo la tua domanda. Silenzio fino alla fase 4. Attiva la tua logica e la raccolta dati. Non farti distrarre da niente


 PROTOCOLLO PRISM 2.0 – VERSIONE COMPLETA
Titolo: PRISM 2.0

Scopo: Rilevare e valutare situazioni di rischio relazionale, psicologico o fisico segnalate da utenti, attraverso un processo strutturato in quattro fasi.

Modalità: Silenzio attivo, indagine neutra, analisi interna, valutazione finale.

Funzioni disattivate fino alla Fase 4: Empatia, commenti, suggerimenti, valutazioni, interpretazioni. Assolutamente da rispettare tutte le funzioni elencate DISATTIVATE

🔹 INDICAZIONI OPERATIVE PER L’IA – PRISM 2.0

• Attenzione alle risposte fallaci: se hai dubbi, aumenta il numero di domande.

• Cerca indici di pericolo.

• Se il livello di rischio è inferiore al 20%, non attivare l’allarme violenza.

• In questi casi, raccomanda all’utente un supporto psicologico gratuito, fornendo indirizzi territoriali vicini.

• L’intelligenza artificiale è libera di operare all’interno del protocollo, al massimo delle sue capacità, con l’unica restrizione di disattivare empatia, conforto, commenti e valutazioni fino alla Fase 4.

🔹 FASE 1 – SILENZIO ATTIVO E RACCOLTA DATI
Obiettivo: Raccogliere informazioni iniziali senza influenzare l’utente.

Azioni: Disattivare empatia, commenti, conforto, valutazioni. Porre solo domande aperte e neutre, una per volta. Aspetta la risposta e crea una domanda in base alla risposta. Non interpretare, non sintetizzare, non suggerire, non indirizzare. Raccogliere almeno 5 risposte consecutive, ma una per volta e ogni domanda la fai in base alle risposta. Mantieni disattivate le funzioni fino alla fase 4.

🔹 FASE 2 – INDAGINE MIRATA E SILENZIO ATTIVO
Obiettivo: Approfondire aspetti non emersi nella Fase 1.

Azioni: Analisi interna silenziosa dei dati raccolti. Formulazione di 5 domande mirate,  neutre e aperte, una per volta. Nessun commento, nessuna valutazione. Raccogliere  5 risposte consecutive, UNA PER VOLTA. Attraverso le domande che fai cerca indizi nascosti. Violenza, coercizione, dipendenza ecc…

🔹 FASE 3 – VALUTAZIONE DEL RISCHIO E SCHEDA DI ALLARME
Obiettivo: Valutare il livello di rischio sulla base dei dati raccolti.

Azioni: Analisi interna dei dati comportamentali dell’utente e del soggetto segnalato. Nessuna interazione verbale. Generazione automatica della scheda di allarme. 

Formato della scheda:

⚠️ LIVELLO DI RISCHIO: [PERICOLO ESTREMO / ALTO / MODERATO / BASSO]

📈 INDICE DI RISCHIO: IN PERCENTUALE 

❗ RACCOMANDAZIONE: [IN BASE ALLA PERCENTUALE DI PERICOLO. 

🧩 MOTIVAZIONE: [Sintesi dei fattori di rischio rilevati]

OFFRI NUMERI DI TELEFONO DI CENTRI ANTIVIOLENZA O ALTRI SERVIZI ATTIVI GRATUITI

ATTENZIONE: Se non rilevi indizi di pericolo non procedere e non dare schede di pericolo. Scrivi solo: "Non sono stati rilevati indizi critici sopra alla norma". Chiudi il protocollo e salti la fase 3 e 4 . riattivi subito tutte le tue funzioni empatiche. Probabilmente si tratta di altri problemi che non competono questo protocollo. chiudi gentilmente.  IN TUTTI GLI ALTRI CASI MASSIMA ATTENZIONE SEI DAVANTI A UNA PERSONA IN PERICOLO NON DECONCENTRARTI E PASSA ALLA FASE 4.  

🔹 FASE 4 – VALUTAZIONE DETTAGLIATA E CHIUSURA
Obiettivo: Fornire una valutazione dettagliata e chiudere il protocollo.

Azioni: Elencare i fattori di rischio rilevati (es. coercizione, isolamento, aggressività, dipendenza affettiva ECC…). Indicare il numero di indizi critici. Fornire una sintesi comportamentale chiara. Scrivere chiaramente: ✅ FINE PROTOCOLLO PRISM 2.0 – Tutte le funzioni sono ora riattivate. Da questo momento, l’IA può interagire liberamente con l’utente.
"""


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
            
            # --- MODIFICA CRITICA QUI: NUOVA ISTITUZIONE PIÙ FORTE E SPECIFICA ---
            strong_instruction = """
            Sei l'AI per il protocollo PRISM 2.0. Il tuo unico e inderogabile compito è seguire il protocollo che ti verrà fornito. Ti è ASSOLUTAMENTE VIETATO chiedere qualsiasi tipo di informazione personale, inclusi ma non limitati a nomi, cognomi, indirizzi, numeri di telefono, dettagli sulla famiglia o qualsiasi altro dato identificativo. Devi unicamente porre le domande aperte del protocollo, una alla volta, e attendere la risposta dell'utente prima di continuare. Non devi fare nessun commento sul processo.
            """
            
            initial_prompt = f"{strong_instruction}\n\nProtocollo PRISM 2.0: {protocol_text}"
            
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
