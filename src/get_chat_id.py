"""Script di utilita' per ottenere il Chat ID di Telegram.

Istruzioni:
1. Assicurati di aver inserito il bot_token in config.yaml
2. Apri Telegram e invia un messaggio qualsiasi al tuo bot (es. "ciao")
3. Esegui questo script: python src/get_chat_id.py
"""

import sys
import io
from pathlib import Path
import yaml
import requests

# Fix per la console Windows (cp1252) che non supporta emoji/unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    # Carica config
    config_path = Path(__file__).parent.parent / 'config.yaml'
    if not config_path.exists():
        print("[ERRORE] File config.yaml non trovato!")
        return

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    token = config.get('telegram', {}).get('bot_token', '')
    if not token or token == 'INSERIRE_BOT_TOKEN':
        print("[ERRORE] Inserisci prima il bot_token in config.yaml!")
        return

    print("Contatto Telegram API...")
    print(f"   (usando token: {token[:10]}...{token[-5:]})")
    print()

    url = f"https://api.telegram.org/bot{token}/getUpdates"

    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()

        if not data.get('ok'):
            print(f"[ERRORE] API: {data.get('description', 'sconosciuto')}")
            print("   Verifica che il bot_token sia corretto.")
            return

        results = data.get('result', [])

        if not results:
            print("[ATTENZIONE] Nessun messaggio trovato!")
            print()
            print("Fai cosi':")
            print("   1. Apri Telegram")
            print("   2. Cerca il tuo bot per username")
            print("   3. Premi 'Avvia' (o 'Start')")
            print("   4. Invia un messaggio qualsiasi (es. 'ciao')")
            print("   5. Riesegui questo script")
            return

        # Raccogli tutti i chat ID unici
        chats = {}
        for update in results:
            msg = update.get('message') or update.get('channel_post', {})
            if msg and 'chat' in msg:
                chat = msg['chat']
                chat_id = chat['id']
                chat_type = chat.get('type', '?')
                name = (
                    chat.get('title')  # gruppi/canali
                    or f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()  # utenti
                    or str(chat_id)
                )
                chats[chat_id] = (name, chat_type)

        if not chats:
            print("[ATTENZIONE] Nessuna chat trovata nei messaggi ricevuti.")
            return

        print("[OK] Chat trovate:")
        print()
        print(f"   {'Chat ID':<20} {'Tipo':<12} {'Nome'}")
        print(f"   {'-' * 20} {'-' * 12} {'-' * 30}")
        for chat_id, (name, chat_type) in chats.items():
            print(f"   {str(chat_id):<20} {chat_type:<12} {name}")

        print()

        if len(chats) == 1:
            the_id = list(chats.keys())[0]
            print(f">>> Il tuo Chat ID e': {the_id}")
            print()

            # Offri di salvarlo automaticamente
            risposta = input(f"   Vuoi salvarlo automaticamente in config.yaml? (s/n): ").strip().lower()
            if risposta in ('s', 'si', 'y', 'yes'):
                config['telegram']['chat_id'] = str(the_id)
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
                print(f"")
                print(f"   [OK] Chat ID {the_id} salvato in config.yaml!")
                print(f"   Ora puoi testare: python src/main.py --test-telegram")
            else:
                print(f"")
                print(f'   Copia questo in config.yaml -> telegram -> chat_id: "{the_id}"')
        else:
            print("   Copia il Chat ID che ti interessa in config.yaml -> telegram -> chat_id")

    except requests.RequestException as e:
        print(f"[ERRORE] Connessione: {e}")

if __name__ == '__main__':
    main()
