# Turing Test dal Vivo (GUI Desktop)

Applicazione desktop minimale per condurre un “Test di Turing dal vivo” con pubblico, con due client: **Esaminatore** e **Umano**. Il server gestisce stato, timer, ritardo LLM e broadcast.

## Requisiti
- Python 3.10+
- Chiave API OpenAI in `OPENAI_API_KEY`

## Installazione
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configurazione
Modifica `config.json` se necessario:
- `host` e `port` del server
- `model` OpenAI
- `llm_delay_seconds` (default 40s)
- `human_timeout_seconds` (default 120s)

## Avvio
Apri tre terminali separati (o macchine diverse sulla stessa LAN):

1) **Server**
```bash
python server.py
```

2) **Esaminatore** (proiettore)
```bash
python examiner_app.py
```

3) **Client Umano**
```bash
python human_client_app.py
```

## Uso in sala con pubblico
- Avvia il server sulla macchina principale.
- L’esaminatore lavora in modalità full-screen e vede le risposte A/B.
- Il client umano risponde da un secondo computer o finestra.
- Ogni domanda attiva un countdown visibile per l’LLM (ritardo di 40s).
- Dopo il 3° round appare il pulsante “Rivela chi è l’AI”.

## UX e scorciatoie
- **Esaminatore**: Invio = invia domanda.
- **Umano**: Ctrl+Invio = invia risposta.

## Robustezza
- Banner di disconnessione del client umano.
- Timeout umano configurabile con pulsante “Salta risposta umano”.
- Errori LLM mostrati come “Errore LLM”.

## Troubleshooting
- **Nessuna risposta LLM**: verifica `OPENAI_API_KEY` e il modello in `config.json`.
- **Client umano disconnesso**: verifica rete LAN e indirizzo `host`/`port`.
- **GUI non parte**: controlla di aver installato `PySide6`.
